"""GLSL shader layer — renders fragment shaders via moderngl into the layer pipeline."""

from __future__ import annotations

import numpy as np
import moderngl

from video_generator.layers import Layer


# Fullscreen quad vertices
_QUAD = np.array([
    -1.0, -1.0,
     1.0, -1.0,
    -1.0,  1.0,
     1.0,  1.0,
], dtype='f4')

_VERTEX_SHADER = """
#version 330
in vec2 in_pos;
out vec2 uv;
void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
    uv = in_pos * 0.5 + 0.5;
}
"""


class ShaderLayer(Layer):
    """Render a GLSL fragment shader as a layer."""

    def __init__(
        self,
        width: int,
        height: int,
        fragment_shader: str,
        seed: int = 0,
    ) -> None:
        self.width = width
        self.height = height
        self.seed = seed

        self.ctx = moderngl.create_context(standalone=True)
        self.prog = self.ctx.program(
            vertex_shader=_VERTEX_SHADER,
            fragment_shader=fragment_shader,
        )
        self.vbo = self.ctx.buffer(_QUAD.tobytes())
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '2f', 'in_pos')])
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((width, height), 3)]
        )

    def render(self, t: float, theta: float) -> np.ndarray:
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0)

        # Set uniforms
        if 'u_time' in self.prog:
            self.prog['u_time'].value = t
        if 'u_theta' in self.prog:
            self.prog['u_theta'].value = theta
        if 'u_resolution' in self.prog:
            self.prog['u_resolution'].value = (float(self.width), float(self.height))
        if 'u_seed' in self.prog:
            self.prog['u_seed'].value = float(self.seed)

        self.vao.render(moderngl.TRIANGLE_STRIP)

        # Read pixels
        data = self.fbo.color_attachments[0].read()
        frame = np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)
        # Flip vertically (OpenGL has origin at bottom-left)
        return frame[::-1].copy()

    def __del__(self):
        try:
            self.ctx.release()
        except Exception:
            pass


# ============================================================
# Shader presets
# ============================================================

SHADER_INFINITE_TUNNEL = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    float angle = atan(p.y, p.x);
    float radius = length(p);

    // Tunnel depth — use theta for seamless loop
    float depth = 1.0 / (radius + 0.1) + u_theta * 2.0;

    // Tile pattern
    float tile = sin(angle * 6.0 + depth * 3.0) * cos(depth * 2.0 - angle * 2.0);

    // Color
    vec3 col = vec3(0.0);
    col.r = 0.02 + 0.03 * sin(depth * 1.5 + u_seed);
    col.g = 0.08 + 0.12 * (0.5 + 0.5 * tile);
    col.b = 0.15 + 0.25 * (0.5 + 0.5 * sin(depth + angle));

    // Glow at center
    col += vec3(0.0, 0.15, 0.2) * (1.0 / (radius * 3.0 + 0.5));

    // Darken edges
    col *= smoothstep(2.0, 0.3, radius);

    fragColor = col;
}
"""

SHADER_MORPHING_CUBES = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

// Rotation matrix
mat2 rot(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }

// Signed distance to a box
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

// Scene SDF
float map(vec3 p) {
    // Repeat space for infinite cubes
    vec3 rep = vec3(3.0);
    vec3 q = mod(p + rep * 0.5, rep) - rep * 0.5;

    // Rotate cubes over time (use theta for loop)
    q.xz *= rot(u_theta + u_seed * 0.1);
    q.yz *= rot(u_theta * 0.7);

    // Morph between cube and sphere
    float morph = 0.5 + 0.5 * sin(u_theta * 2.0);
    float box = sdBox(q, vec3(0.5 * (1.0 + 0.3 * sin(u_theta))));
    float sphere = length(q) - 0.6;
    return mix(box, sphere, morph * 0.4);
}

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    // Camera — moving forward through the cube field
    vec3 ro = vec3(0.0, 0.0, u_theta * 3.0);
    vec3 rd = normalize(vec3(p, 1.5));
    rd.xz *= rot(sin(u_theta * 0.3) * 0.3);
    rd.yz *= rot(cos(u_theta * 0.2) * 0.2);

    // Ray march
    float t = 0.0;
    float d;
    for (int i = 0; i < 80; i++) {
        d = map(ro + rd * t);
        if (d < 0.001 || t > 30.0) break;
        t += d;
    }

    // Shading
    vec3 col = vec3(0.02, 0.03, 0.08); // dark bg
    if (t < 30.0) {
        // Normal for lighting
        vec3 pos = ro + rd * t;
        vec2 e = vec2(0.001, 0.0);
        vec3 n = normalize(vec3(
            map(pos + e.xyy) - map(pos - e.xyy),
            map(pos + e.yxy) - map(pos - e.yxy),
            map(pos + e.yyx) - map(pos - e.yyx)
        ));

        // Teal/cyan lighting
        float diff = max(dot(n, normalize(vec3(1.0, 1.0, -1.0))), 0.0);
        float spec = pow(max(dot(reflect(rd, n), normalize(vec3(1.0, 1.0, -1.0))), 0.0), 32.0);

        col = vec3(0.0, 0.12, 0.18) * 0.3; // ambient
        col += vec3(0.0, 0.5, 0.6) * diff * 0.6;  // diffuse teal
        col += vec3(0.3, 0.8, 1.0) * spec * 0.4;  // specular highlight

        // Distance fog
        col = mix(col, vec3(0.02, 0.03, 0.08), 1.0 - exp(-t * 0.08));
    }

    fragColor = col;
}
"""

SHADER_SACRED_GEOMETRY = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    float angle = atan(p.y, p.x);
    float radius = length(p);

    // Rotating sacred geometry pattern
    float rot_speed = u_theta;
    vec3 col = vec3(0.02, 0.02, 0.06);

    // Multiple layered geometric rings
    for (int i = 0; i < 6; i++) {
        float fi = float(i);
        float r = 0.2 + fi * 0.15;
        float n_sides = 3.0 + fi; // triangle, square, pentagon, hex...
        float rot = rot_speed * (0.5 + fi * 0.15) + u_seed * 0.5;

        // Polygon edge distance
        float a = angle + rot;
        float sector = 6.283185 / n_sides;
        float half_sector = sector * 0.5;
        float a_mod = mod(a + half_sector, sector) - half_sector;
        float poly_dist = abs(radius - r * cos(half_sector) / cos(a_mod));

        // Glow on edges
        float glow = 0.003 / (poly_dist + 0.003);

        // Color per layer
        vec3 layer_col;
        if (mod(fi, 3.0) == 0.0) layer_col = vec3(0.0, 0.6, 0.55);
        else if (mod(fi, 3.0) == 1.0) layer_col = vec3(0.1, 0.3, 0.7);
        else layer_col = vec3(0.4, 0.1, 0.6);

        col += layer_col * glow * 0.15;
    }

    // Central glow
    col += vec3(0.0, 0.3, 0.35) * (0.05 / (radius + 0.05));

    // Pulsing brightness
    col *= 0.8 + 0.2 * sin(u_theta * 3.0);

    // Vignette
    col *= smoothstep(1.5, 0.4, radius);

    fragColor = col;
}
"""

SHADER_WIREFRAME_TERRAIN = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

// Simple hash for terrain height
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1 + u_seed, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}

float terrain(vec2 p) {
    float h = 0.0;
    h += noise(p * 1.0) * 0.5;
    h += noise(p * 2.0) * 0.25;
    h += noise(p * 4.0) * 0.125;
    return h;
}

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    vec3 col = vec3(0.01, 0.02, 0.06);

    // Grid lines — perspective terrain
    float z_offset = u_theta * 4.0; // forward movement, loops with theta

    for (int i = 0; i < 30; i++) {
        float z = float(i) * 0.3 + mod(z_offset, 0.3);
        float perspective = 1.0 / (z + 0.5);

        // Ground plane y position
        float ground_y = -0.3 * perspective + 0.1;

        // Terrain height at this z
        float h = terrain(vec2(p.x / perspective * 2.0, z + z_offset)) * 0.3;
        ground_y += h * perspective;

        // Horizontal grid line
        float line = abs(p.y - ground_y);
        float glow = 0.001 / (line + 0.001) * perspective * 0.3;

        // Color fades with distance
        vec3 line_col = mix(vec3(0.0, 0.5, 0.6), vec3(0.0, 0.1, 0.2), z / 10.0);
        col += line_col * glow * 0.05;

        // Vertical grid lines
        float grid_x = 0.5 * perspective;
        float vline = abs(mod(p.x + grid_x * 0.5, grid_x) - grid_x * 0.5);
        float vglow = 0.001 / (vline + 0.001) * perspective * 0.2;
        if (p.y < ground_y + 0.02) {
            col += line_col * vglow * 0.03;
        }
    }

    // Horizon glow
    col += vec3(0.0, 0.15, 0.2) * smoothstep(0.3, -0.1, p.y) * 0.5;

    // Stars
    float star = hash(floor(p * 80.0));
    if (star > 0.98 && p.y > 0.0) {
        col += vec3(0.3, 0.4, 0.5) * (star - 0.98) * 50.0;
    }

    fragColor = col;
}
"""


# Registry of available shader presets
SHADER_PRESETS = {
    "tunnel": SHADER_INFINITE_TUNNEL,
    "cubes": SHADER_MORPHING_CUBES,
    "geometry": SHADER_SACRED_GEOMETRY,
    "terrain": SHADER_WIREFRAME_TERRAIN,
}
