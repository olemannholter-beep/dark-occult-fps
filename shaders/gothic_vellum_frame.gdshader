shader_type canvas_item;

uniform vec4 tint_color : source_color = vec4(0.95, 0.78, 0.36, 1.0);
uniform float border_glow : hint_range(0.0, 2.0) = 0.48;
uniform float vellum_grain_strength : hint_range(0.0, 1.0) = 0.20;
uniform float panel_opacity : hint_range(0.0, 1.0) = 0.96;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm_vellum(vec2 p) {
	float v = 0.0;
	float amp = 0.5;
	mat2 rot = mat2(vec2(0.8, -0.6), vec2(0.6, 0.8));
	for (int i = 0; i < 4; i++) {
		v += amp * value_noise(p);
		p = rot * p * 2.04 + vec2(17.1, 31.7);
		amp *= 0.5;
	}
	return v;
}

void fragment() {
	vec2 uv = UV;
	vec2 centered = (uv - vec2(0.5)) * 2.0;
	float radial_dist = clamp(length(centered * vec2(0.92, 0.98)), 0.0, 1.35);
	float vignette = smoothstep(0.15, 1.18, radial_dist);

	float coarse_grain = fbm_vellum(uv * vec2(28.0, 20.0));
	float fine_fiber = fbm_vellum(uv * vec2(120.0, 88.0));
	float grain = (coarse_grain * 0.68 + fine_fiber * 0.32) - 0.5;

	vec3 center_col = vec3(0.14, 0.12, 0.18);
	vec3 edge_col = vec3(0.08, 0.07, 0.11);
	vec3 base_vellum = mix(center_col, edge_col, vignette);
	base_vellum += tint_color.rgb * (grain * 0.04 * vellum_grain_strength);

	vec2 edge_dist_xy = min(uv, vec2(1.0) - uv);
	float min_edge = min(edge_dist_xy.x, edge_dist_xy.y);
	float border_mask = 1.0 - smoothstep(0.0, 0.045, min_edge);
	float inner_filigree_mask = smoothstep(0.012, 0.018, min_edge) * (1.0 - smoothstep(0.018, 0.026, min_edge));

	float candle_shimmer = 0.5 + 0.5 * sin(TIME * 1.4 + uv.x * 6.0 + uv.y * 4.0);
	float ember_wave = 0.5 + 0.5 * cos(TIME * 0.85 - uv.x * 4.5 + uv.y * 5.2);
	float shimmer_factor = mix(0.75, 1.25, candle_shimmer * 0.65 + ember_wave * 0.35);

	vec3 gilded_shimmer = tint_color.rgb * border_glow * shimmer_factor * (border_mask * 0.50 + inner_filigree_mask * 0.65);
	vec3 final_rgb = base_vellum + gilded_shimmer;

	COLOR = vec4(final_rgb, panel_opacity);
}
