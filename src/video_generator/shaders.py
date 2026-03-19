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
    float depth = 1.0 / (radius + 0.05) + u_theta * 3.0;

    // Multiple layered patterns for richness
    float pattern1 = sin(angle * 8.0 + depth * 2.0) * 0.5 + 0.5;
    float pattern2 = sin(angle * 4.0 - depth * 1.5 + 1.0) * 0.5 + 0.5;
    float pattern3 = sin(depth * 4.0 + sin(angle * 3.0) * 2.0) * 0.5 + 0.5;

    // Hexagonal-ish grid lines in the tunnel
    float grid = smoothstep(0.45, 0.5, pattern1) + smoothstep(0.45, 0.5, pattern2) * 0.5;

    // Base color — deep dark blue
    vec3 col = vec3(0.01, 0.02, 0.05);

    // Tunnel walls with teal glow on grid lines
    col += vec3(0.0, 0.15, 0.2) * grid * (1.0 / (radius * 2.0 + 0.3));

    // Depth-based color shift (closer = brighter teal, far = deep blue)
    col += vec3(0.0, 0.08, 0.12) * pattern3 * (1.0 / (radius * 1.5 + 0.5));

    // Bright center glow (the light at the end of the tunnel)
    float center_glow = exp(-radius * 4.0);
    col += vec3(0.05, 0.3, 0.35) * center_glow;

    // Subtle warm accent streaks
    float streak = pow(pattern1 * pattern2, 3.0);
    col += vec3(0.1, 0.05, 0.0) * streak * (1.0 / (radius + 0.5)) * 0.3;

    // Vignette
    col *= smoothstep(2.0, 0.2, radius);

    // Slight gamma for richness
    col = pow(col, vec3(0.9));

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

mat2 rot(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float sdSphere(vec3 p, float r) { return length(p) - r; }

float map(vec3 p) {
    // Repeat space — wider spacing for breathing room
    vec3 rep = vec3(4.0);
    vec3 q = mod(p + rep * 0.5, rep) - rep * 0.5;

    // Slow gentle rotation — integer multiples for seamless loop
    q.xz *= rot(u_theta * 1.0 + u_seed * 0.1);
    q.yz *= rot(u_theta * 1.0);

    // Smooth morph between cube and sphere — integer multiple
    float morph = 0.5 + 0.5 * sin(u_theta * 2.0);
    float size = 0.6 + 0.15 * sin(u_theta * 1.0);
    float box = sdBox(q, vec3(size));
    float sphere = sdSphere(q, size * 1.1);
    return mix(box, sphere, morph * 0.5);
}

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    // Camera — slow drift forward, gentle sway (integer multiples for loop)
    vec3 ro = vec3(
        sin(u_theta * 1.0) * 1.5,
        cos(u_theta * 1.0) * 0.8,
        u_theta * 1.5
    );
    vec3 rd = normalize(vec3(p * 0.8, 1.5));
    rd.xz *= rot(sin(u_theta * 1.0) * 0.15);
    rd.yz *= rot(cos(u_theta * 1.0) * 0.1);

    // Ray march
    float t = 0.0;
    float d;
    float glow = 0.0;
    for (int i = 0; i < 64; i++) {
        d = map(ro + rd * t);
        // Accumulate glow from near-misses
        glow += 0.02 / (abs(d) + 0.05);
        if (d < 0.002 || t > 40.0) break;
        t += d * 0.8; // slightly smaller steps for smoother result
    }

    // Dark background
    vec3 col = vec3(0.01, 0.02, 0.05);

    // Volumetric glow from near-misses (soft ambient light)
    col += vec3(0.0, 0.06, 0.08) * glow * 0.015;

    if (t < 40.0) {
        vec3 pos = ro + rd * t;
        vec2 e = vec2(0.002, 0.0);
        vec3 n = normalize(vec3(
            map(pos + e.xyy) - map(pos - e.xyy),
            map(pos + e.yxy) - map(pos - e.yxy),
            map(pos + e.yyx) - map(pos - e.yyx)
        ));

        // Soft lighting from two directions
        vec3 light1 = normalize(vec3(1.0, 1.0, -0.5));
        vec3 light2 = normalize(vec3(-0.5, -0.3, 1.0));
        float diff1 = max(dot(n, light1), 0.0);
        float diff2 = max(dot(n, light2), 0.0);
        float spec = pow(max(dot(reflect(rd, n), light1), 0.0), 16.0);

        // Gentle teal/blue surface
        col = vec3(0.01, 0.04, 0.06); // ambient
        col += vec3(0.0, 0.25, 0.3) * diff1 * 0.5;   // main light teal
        col += vec3(0.05, 0.1, 0.2) * diff2 * 0.3;    // fill light blue
        col += vec3(0.2, 0.5, 0.6) * spec * 0.2;      // subtle specular

        // Edge glow (fresnel)
        float fresnel = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);
        col += vec3(0.0, 0.2, 0.25) * fresnel * 0.4;

        // Distance fog — smooth fade
        col = mix(col, vec3(0.01, 0.02, 0.05), 1.0 - exp(-t * 0.05));
    }

    // Subtle vignette
    float vig = 1.0 - length(p) * 0.3;
    col *= max(vig, 0.0);

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

    vec3 col = vec3(0.01, 0.01, 0.04);

    // Flower of life — overlapping circles
    for (int i = 0; i < 6; i++) {
        float fi = float(i);
        float a = fi * 3.14159 / 3.0 + u_theta * 1.0;
        vec2 center = vec2(cos(a), sin(a)) * 0.35;
        float d = abs(length(p - center) - 0.35);
        float glow = 0.002 / (d + 0.002);
        col += vec3(0.0, 0.15, 0.18) * glow * 0.08;
    }
    // Center circle
    float cd = abs(length(p) - 0.35);
    col += vec3(0.0, 0.12, 0.15) * 0.002 / (cd + 0.002) * 0.08;

    // Nested polygons — triangle through nonagon, each rotating differently
    for (int i = 0; i < 8; i++) {
        float fi = float(i);
        float r = 0.12 + fi * 0.12;
        float n_sides = 3.0 + fi;
        // Alternate rotation directions, different speeds
        float dir = mod(fi, 2.0) == 0.0 ? 1.0 : -1.0;
        float rot = u_theta * (1.0 + fi) * dir + u_seed * 0.3 + fi * 0.5;

        float a = angle + rot;
        float sector = 6.283185 / n_sides;
        float half_sector = sector * 0.5;
        float a_mod = mod(a + half_sector, sector) - half_sector;
        float poly_dist = abs(radius - r * cos(half_sector) / cos(a_mod));

        float glow = 0.0015 / (poly_dist + 0.0015);

        // Color gradient across layers — teal to blue to purple
        vec3 layer_col;
        float t = fi / 7.0;
        layer_col = mix(vec3(0.0, 0.5, 0.5), vec3(0.3, 0.15, 0.6), t);

        col += layer_col * glow * 0.1;
    }

    // Radiating lines from center
    for (int i = 0; i < 12; i++) {
        float a = float(i) * 3.14159 / 6.0 + u_theta * 1.0;
        vec2 dir = vec2(cos(a), sin(a));
        float line_dist = abs(dot(p, vec2(-dir.y, dir.x)));
        float line_glow = 0.001 / (line_dist + 0.001) * smoothstep(0.0, 0.15, radius) * smoothstep(1.2, 0.3, radius);
        col += vec3(0.0, 0.08, 0.1) * line_glow * 0.04;
    }

    // Pulsing outer ring
    float outer = abs(radius - 0.95 - 0.05 * sin(u_theta * 2.0));
    col += vec3(0.0, 0.2, 0.25) * 0.003 / (outer + 0.003) * 0.15;

    // Central glow — soft and warm
    float center_glow = exp(-radius * 3.0);
    col += vec3(0.05, 0.2, 0.25) * center_glow * 0.5;

    // Gentle pulse
    col *= 0.85 + 0.15 * sin(u_theta * 2.0);

    // Vignette
    col *= smoothstep(1.6, 0.3, radius);

    // Gamma
    col = pow(col, vec3(0.95));

    fragColor = col;
}
"""

SHADER_ENERGY_ORB = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1 + u_seed, 311.7))) * 43758.5453);
}

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    float radius = length(p);
    float angle = atan(p.y, p.x);

    vec3 col = vec3(0.01, 0.015, 0.04);

    // Central orb — glowing sphere
    float orb_r = 0.35 + 0.03 * sin(u_theta * 3.0);
    float orb_dist = radius - orb_r;

    // Orb surface glow
    float surface = 0.005 / (abs(orb_dist) + 0.005);
    col += vec3(0.0, 0.3, 0.35) * surface * 0.3;

    // Inner orb fill — bright gradient
    if (radius < orb_r) {
        float inner = 1.0 - radius / orb_r;
        // Swirling noise inside the orb
        float swirl1 = sin(angle * 4.0 + u_theta * 2.0 + radius * 8.0) * 0.5 + 0.5;
        float swirl2 = sin(angle * 6.0 - u_theta * 2.0 + radius * 12.0) * 0.5 + 0.5;
        float pattern = swirl1 * 0.6 + swirl2 * 0.4;

        col += vec3(0.0, 0.15, 0.2) * inner * 0.8;
        col += vec3(0.0, 0.25, 0.3) * pattern * inner * 0.4;
        col += vec3(0.1, 0.4, 0.45) * pow(inner, 3.0) * 0.6; // bright center
    }

    // Energy tendrils radiating outward
    for (int i = 0; i < 8; i++) {
        float fi = float(i);
        float tendril_angle = fi * 3.14159 * 2.0 / 8.0 + u_theta * 1.0 + sin(u_theta * 1.0 + fi) * 0.3;
        vec2 dir = vec2(cos(tendril_angle), sin(tendril_angle));

        // Distance from this tendril line
        float d = abs(dot(p, vec2(-dir.y, dir.x)));

        // Only show outside the orb, fade with distance
        float mask = smoothstep(orb_r - 0.05, orb_r + 0.1, radius) * smoothstep(1.5, orb_r + 0.1, radius);

        // Wavy tendril
        float wave = sin(radius * 15.0 - u_theta * 4.0 + fi * 2.0) * 0.02;
        d += wave;

        float glow = 0.003 / (abs(d) + 0.003) * mask;
        col += vec3(0.0, 0.12, 0.15) * glow * 0.15;
    }

    // Orbiting particles (dots circling the orb)
    for (int i = 0; i < 12; i++) {
        float fi = float(i);
        float orbit_r = 0.5 + fi * 0.06;
        float orbit_speed = 0.3 + fi * 0.05;
        float orbit_angle = u_theta * orbit_speed + fi * 1.2 + u_seed;

        vec2 particle_pos = vec2(cos(orbit_angle), sin(orbit_angle)) * orbit_r;
        float d = length(p - particle_pos);
        float glow = 0.003 / (d + 0.003);

        vec3 pcol = mix(vec3(0.0, 0.4, 0.45), vec3(0.1, 0.2, 0.5), fi / 12.0);
        col += pcol * glow * 0.08;
    }

    // Ambient haze around orb
    float haze = exp(-radius * 2.0) * 0.15;
    col += vec3(0.0, 0.1, 0.15) * haze;

    // Subtle stars in background
    float star = hash(floor(p * 60.0));
    if (star > 0.985 && radius > orb_r + 0.2) {
        col += vec3(0.15, 0.2, 0.25) * (star - 0.985) * 60.0;
    }

    // Vignette
    col *= smoothstep(1.8, 0.3, radius);

    fragColor = col;
}
"""


SHADER_TORUS_KNOT = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

mat2 rot(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }

// Torus SDF
float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

float map(vec3 p) {
    // Rotate the whole scene slowly
    p.xz *= rot(u_theta * 1.0);
    p.xy *= rot(u_theta * 1.0 * 0.3);

    // Twist space along y-axis for knot effect
    float twist = p.y * 1.5 + u_theta * 2.0;
    p.xz *= rot(twist);

    // Torus with morphing thickness
    float thickness = 0.15 + 0.05 * sin(u_theta * 2.0);
    float d = sdTorus(p, vec2(0.8, thickness));

    // Add a second smaller torus rotated differently
    vec3 p2 = p;
    p2.xy *= rot(1.57);
    float d2 = sdTorus(p2, vec2(0.6, thickness * 0.7));

    return min(d, d2);
}

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    vec3 ro = vec3(0.0, 0.0, -3.0);
    vec3 rd = normalize(vec3(p, 1.5));

    float t = 0.0;
    float glow = 0.0;
    for (int i = 0; i < 80; i++) {
        float d = map(ro + rd * t);
        glow += 0.015 / (abs(d) + 0.03);
        if (d < 0.001 || t > 20.0) break;
        t += d;
    }

    vec3 col = vec3(0.01, 0.015, 0.04);
    col += vec3(0.0, 0.05, 0.07) * glow * 0.012;

    if (t < 20.0) {
        vec3 pos = ro + rd * t;
        vec2 e = vec2(0.001, 0.0);
        vec3 n = normalize(vec3(
            map(pos + e.xyy) - map(pos - e.xyy),
            map(pos + e.yxy) - map(pos - e.yxy),
            map(pos + e.yyx) - map(pos - e.yyx)
        ));

        vec3 light = normalize(vec3(1.0, 1.0, -1.0));
        float diff = max(dot(n, light), 0.0);
        float spec = pow(max(dot(reflect(rd, n), light), 0.0), 24.0);
        float fresnel = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);

        col = vec3(0.01, 0.03, 0.05);
        col += vec3(0.0, 0.3, 0.35) * diff * 0.5;
        col += vec3(0.1, 0.15, 0.3) * spec * 0.3;
        col += vec3(0.0, 0.2, 0.25) * fresnel * 0.4;

        col = mix(col, vec3(0.01, 0.015, 0.04), 1.0 - exp(-t * 0.1));
    }

    col *= 1.0 - length(p) * 0.25;
    fragColor = col;
}
"""

SHADER_OCTAHEDRON = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

mat2 rot(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }

float sdOctahedron(vec3 p, float s) {
    p = abs(p);
    return (p.x + p.y + p.z - s) * 0.57735027;
}

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float map(vec3 p) {
    // Slow rotation
    p.xz *= rot(u_theta * 1.0);
    p.yz *= rot(u_theta * 1.0 * 0.7);
    p.xy *= rot(u_theta * 1.0 * 0.4);

    // Morph between octahedron and box
    float morph = 0.5 + 0.5 * sin(u_theta * 1.0);
    float oct = sdOctahedron(p, 1.0 + 0.2 * sin(u_theta * 2.0));
    float box = sdBox(p, vec3(0.7 + 0.1 * sin(u_theta * 3.0)));
    float d = mix(oct, box, morph * 0.6);

    // Subtract inner shape for hollow feel
    float inner = sdOctahedron(p, 0.6);
    d = max(d, -inner);

    return d;
}

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    vec3 ro = vec3(0.0, 0.0, -3.5);
    vec3 rd = normalize(vec3(p, 1.5));
    // Gentle camera sway
    rd.xz *= rot(sin(u_theta * 1.0) * 0.1);

    float t = 0.0;
    float glow = 0.0;
    for (int i = 0; i < 80; i++) {
        float d = map(ro + rd * t);
        glow += 0.02 / (abs(d) + 0.04);
        if (d < 0.001 || t > 20.0) break;
        t += d;
    }

    vec3 col = vec3(0.01, 0.012, 0.035);
    col += vec3(0.02, 0.04, 0.06) * glow * 0.01;

    if (t < 20.0) {
        vec3 pos = ro + rd * t;
        vec2 e = vec2(0.001, 0.0);
        vec3 n = normalize(vec3(
            map(pos + e.xyy) - map(pos - e.xyy),
            map(pos + e.yxy) - map(pos - e.yxy),
            map(pos + e.yyx) - map(pos - e.yyx)
        ));

        vec3 light1 = normalize(vec3(1.0, 1.0, -1.0));
        vec3 light2 = normalize(vec3(-1.0, 0.5, 0.5));
        float diff1 = max(dot(n, light1), 0.0);
        float diff2 = max(dot(n, light2), 0.0);
        float spec = pow(max(dot(reflect(rd, n), light1), 0.0), 32.0);
        float fresnel = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);

        col = vec3(0.01, 0.02, 0.04);
        col += vec3(0.0, 0.2, 0.3) * diff1 * 0.5;
        col += vec3(0.1, 0.05, 0.2) * diff2 * 0.3;
        col += vec3(0.2, 0.4, 0.6) * spec * 0.3;
        col += vec3(0.0, 0.15, 0.25) * fresnel * 0.5;

        col = mix(col, vec3(0.01, 0.012, 0.035), 1.0 - exp(-t * 0.08));
    }

    col *= 1.0 - length(p) * 0.2;
    fragColor = col;
}
"""

SHADER_WARP = """
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

    float radius = length(p);
    float angle = atan(p.y, p.x);

    vec3 col = vec3(0.01, 0.015, 0.04);

    // Warp field — concentric distorted rings moving outward
    for (int i = 0; i < 5; i++) {
        float fi = float(i);
        // Rings expanding outward
        float ring_r = mod(fi * 0.25 + u_theta * 1.0 / 6.283, 1.3);

        // Distorted ring
        float distortion = sin(angle * (3.0 + fi) + u_theta * 2.0) * 0.08;
        float d = abs(radius - ring_r + distortion);

        float glow = 0.003 / (d + 0.003);
        glow *= smoothstep(1.3, 0.1, ring_r); // fade as ring expands

        vec3 ring_col = mix(vec3(0.0, 0.4, 0.45), vec3(0.1, 0.15, 0.4), fi / 5.0);
        col += ring_col * glow * 0.12;
    }

    // Central star/warp point
    float star_glow = 0.02 / (radius + 0.02);
    col += vec3(0.1, 0.4, 0.5) * star_glow * 0.4;

    // Speed lines radiating from center
    for (int i = 0; i < 20; i++) {
        float fi = float(i);
        float line_angle = fi * 6.283 / 20.0 + u_seed;
        float a_diff = abs(mod(angle - line_angle + 3.14159, 6.283) - 3.14159);
        float line = 0.003 / (a_diff + 0.003);
        line *= smoothstep(0.1, 0.4, radius) * smoothstep(1.5, 0.5, radius);

        // Animate length
        float pulse = 0.5 + 0.5 * sin(u_theta * 3.0 + fi * 0.8);
        col += vec3(0.0, 0.08, 0.1) * line * pulse * 0.02;
    }

    // Pulsing brightness
    col *= 0.9 + 0.1 * sin(u_theta * 2.0);

    col *= smoothstep(1.8, 0.2, radius);
    fragColor = col;
}
"""

SHADER_DNA_HELIX = """
#version 330
in vec2 uv;
out vec3 fragColor;
uniform float u_time;
uniform float u_theta;
uniform vec2 u_resolution;
uniform float u_seed;

mat2 rot(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }

float sdSphere(vec3 p, float r) { return length(p) - r; }

float map(vec3 p) {
    // Two helical strands
    float d = 1e10;

    for (int i = 0; i < 24; i++) {
        float fi = float(i);
        float y = fi * 0.25 - 3.0;

        // Helix 1
        float a1 = y * 2.5 + u_theta * 2.0;
        vec3 p1 = vec3(cos(a1) * 0.5, y, sin(a1) * 0.5);
        d = min(d, sdSphere(p - p1, 0.08));

        // Helix 2 (opposite side)
        float a2 = a1 + 3.14159;
        vec3 p2 = vec3(cos(a2) * 0.5, y, sin(a2) * 0.5);
        d = min(d, sdSphere(p - p2, 0.08));

        // Connecting rungs (every 3rd node)
        if (mod(fi, 3.0) < 1.0) {
            // Capsule between p1 and p2
            vec3 mid = (p1 + p2) * 0.5;
            d = min(d, sdSphere(p - mid, 0.04));
            d = min(d, sdSphere(p - mix(p1, p2, 0.25), 0.03));
            d = min(d, sdSphere(p - mix(p1, p2, 0.75), 0.03));
        }
    }

    return d;
}

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    p.x *= u_resolution.x / u_resolution.y;

    // Camera slowly orbits
    float cam_angle = u_theta * 1.0;
    vec3 ro = vec3(sin(cam_angle) * 3.0, 0.0, cos(cam_angle) * 3.0);
    vec3 target = vec3(0.0, 0.0, 0.0);
    vec3 fwd = normalize(target - ro);
    vec3 right = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, fwd);
    vec3 rd = normalize(fwd * 1.5 + right * p.x + up * p.y);

    float t = 0.0;
    float glow = 0.0;
    for (int i = 0; i < 80; i++) {
        float d = map(ro + rd * t);
        glow += 0.015 / (abs(d) + 0.03);
        if (d < 0.001 || t > 20.0) break;
        t += d;
    }

    vec3 col = vec3(0.01, 0.015, 0.04);
    col += vec3(0.0, 0.04, 0.06) * glow * 0.01;

    if (t < 20.0) {
        vec3 pos = ro + rd * t;
        vec2 e = vec2(0.001, 0.0);
        vec3 n = normalize(vec3(
            map(pos + e.xyy) - map(pos - e.xyy),
            map(pos + e.yxy) - map(pos - e.yxy),
            map(pos + e.yyx) - map(pos - e.yyx)
        ));

        vec3 light = normalize(vec3(1.0, 1.0, -0.5));
        float diff = max(dot(n, light), 0.0);
        float spec = pow(max(dot(reflect(rd, n), light), 0.0), 20.0);
        float fresnel = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);

        col = vec3(0.01, 0.03, 0.05);
        col += vec3(0.0, 0.3, 0.35) * diff * 0.5;
        col += vec3(0.15, 0.3, 0.5) * spec * 0.3;
        col += vec3(0.0, 0.2, 0.3) * fresnel * 0.4;

        col = mix(col, vec3(0.01, 0.015, 0.04), 1.0 - exp(-t * 0.1));
    }

    col *= 1.0 - length(p) * 0.2;
    fragColor = col;
}
"""


# Registry of available shader presets
SHADER_PRESETS = {
    "tunnel": SHADER_INFINITE_TUNNEL,
    "cubes": SHADER_MORPHING_CUBES,
    "geometry": SHADER_SACRED_GEOMETRY,
    "orb": SHADER_ENERGY_ORB,
    "torus": SHADER_TORUS_KNOT,
    "octahedron": SHADER_OCTAHEDRON,
    "warp": SHADER_WARP,
    "dna": SHADER_DNA_HELIX,
}
