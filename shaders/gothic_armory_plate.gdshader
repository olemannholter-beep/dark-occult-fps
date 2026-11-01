shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 albedo_color : source_color = vec4(0.1216, 0.1255, 0.1412, 1.0); // #1f2024 Blackened Iron
uniform vec4 edge_wear_color : source_color = vec4(0.42, 0.44, 0.48, 1.0);
uniform float metallic_val : hint_range(0.0, 1.0) = 0.85;
uniform float roughness_val : hint_range(0.0, 1.0) = 0.45;
uniform float specular_val : hint_range(0.0, 1.0) = 0.25;

uniform vec4 emission_color : source_color = vec4(0.8510, 0.2510, 0.0784, 1.0); // #d94014 Cinder Rune
uniform float emission_energy : hint_range(0.0, 8.0) = 0.0;

uniform float triplanar_scale : hint_range(1.0, 64.0) = 22.0;
uniform float macro_patina_scale : hint_range(0.5, 16.0) = 4.5;
uniform float grain_strength : hint_range(0.0, 0.35) = 0.12;
uniform float edge_wear_strength : hint_range(0.0, 1.0) = 0.38;
uniform float use_vertex_color : hint_range(0.0, 1.0) = 1.0;

varying vec3 v_local_pos;
varying vec3 v_local_norm;

float _hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float _value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = _hash12(i + vec2(0.0, 0.0));
	float b = _hash12(i + vec2(1.0, 0.0));
	float c = _hash12(i + vec2(0.0, 1.0));
	float d = _hash12(i + vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float _triplanar_noise(vec3 pos, vec3 norm, float scale) {
	vec3 w = abs(norm);
	w = max(w - 0.15, 0.0001);
	w /= (w.x + w.y + w.z);

	vec2 uv_x = pos.yz * scale;
	vec2 uv_y = pos.xz * scale;
	vec2 uv_z = pos.xy * scale;

	float nx = _value_noise(uv_x) * 0.65 + _value_noise(uv_x * 2.7) * 0.35;
	float ny = _value_noise(uv_y) * 0.65 + _value_noise(uv_y * 2.7) * 0.35;
	float nz = _value_noise(uv_z) * 0.65 + _value_noise(uv_z * 2.7) * 0.35;

	return nx * w.x + ny * w.y + nz * w.z;
}

void vertex() {
	v_local_pos = VERTEX;
	v_local_norm = normalize(NORMAL);
}

void fragment() {
	// Quantize local position to the 7mm (0.007m) micro-voxel grid so each voxel face has razor-sharp uniform shading
	vec3 vox_pos = floor(v_local_pos / 0.007) * 0.007;
	float fine_hammer = _triplanar_noise(vox_pos, v_local_norm, triplanar_scale);
	float macro_patina = _triplanar_noise(vox_pos, v_local_norm, macro_patina_scale);
	float combined_grain = mix(macro_patina, fine_hammer, 0.62);
	float grain_mod = mix(1.0 - grain_strength * 0.40, 1.0 + grain_strength * 0.40, combined_grain);

	// COLOR.rgb encoding:
	// - New 7mm micro-voxel format: R = Crevice AO + ±8% Value Jitter (0.50..1.0), G = Raised 1-Voxel Edge Highlight (0.0..1.0), B = Warmth Jitter (0.42..0.58)
	// - Legacy format fallback when R == G == B
	bool is_packed_ao_edge = (abs(COLOR.r - COLOR.g) + abs(COLOR.g - COLOR.b)) > 0.03;
	float crevice_ao = clamp(COLOR.r, 0.48, 1.04);
	float raised_edge = is_packed_ao_edge ? clamp(COLOR.g, 0.0, 1.0) : smoothstep(0.88, 0.99, crevice_ao);
	float warmth_shift = is_packed_ao_edge ? clamp((COLOR.b - 0.50) * 0.18, -0.10, 0.10) : 0.0;

	vec3 warm_jitter_tint = vec3(1.0 + warmth_shift, 1.0 + warmth_shift * 0.45, 1.0 - warmth_shift);
	// Directional flat-voxel face contrast so individual 7mm cube faces catch light crisply
	float flat_face_light = 0.92 + 0.10 * max(0.0, v_local_norm.y) + 0.05 * abs(v_local_norm.z);

	vec3 base_col = albedo_color.rgb * warm_jitter_tint * mix(1.0, crevice_ao * flat_face_light, use_vertex_color) * grain_mod;
	vec3 worn_edge_col = mix(albedo_color.rgb * 1.32, edge_wear_color.rgb, 0.45 + metallic_val * 0.45);
	ALBEDO = mix(base_col, worn_edge_col * clamp(crevice_ao + 0.18, 0.72, 1.12), raised_edge * edge_wear_strength * 0.62);

	METALLIC = clamp(metallic_val + raised_edge * 0.08 * metallic_val, 0.0, 1.0);
	float recess_rough_boost = (1.0 - clamp(crevice_ao, 0.0, 1.0)) * 0.28;
	float edge_polish = raised_edge * 0.10 * metallic_val;
	ROUGHNESS = clamp(roughness_val + recess_rough_boost - edge_polish + (combined_grain - 0.5) * grain_strength * 0.30, 0.08, 0.98);
	SPECULAR = specular_val;

	// Keep EMISSION independent of vertex COLOR.rgb so emissive eyes & candle flames exceed the HDR threshold
	EMISSION = emission_color.rgb * emission_energy;
}
