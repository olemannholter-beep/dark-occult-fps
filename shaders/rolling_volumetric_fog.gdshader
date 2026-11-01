shader_type fog;

uniform float base_density : hint_range(0.0, 1.0) = 0.085;
uniform float trough_density : hint_range(0.0, 1.0) = 0.005;
uniform float height_falloff : hint_range(0.05, 2.0) = 0.35;
uniform float base_height = 4.2;
uniform vec3 fog_albedo : source_color = vec3(0.18, 0.17, 0.24);
uniform vec3 fog_emission : source_color = vec3(0.025, 0.02, 0.04);

float hash3d(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yxz + 33.33);
	return fract((p.x + p.y) * p.z);
}

float noise3d(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);

	return mix(
		mix(
			mix(hash3d(i + vec3(0.0, 0.0, 0.0)), hash3d(i + vec3(1.0, 0.0, 0.0)), f.x),
			mix(hash3d(i + vec3(0.0, 1.0, 0.0)), hash3d(i + vec3(1.0, 1.0, 0.0)), f.x),
			f.y
		),
		mix(
			mix(hash3d(i + vec3(0.0, 0.0, 1.0)), hash3d(i + vec3(1.0, 0.0, 1.0)), f.x),
			mix(hash3d(i + vec3(0.0, 1.0, 1.0)), hash3d(i + vec3(1.0, 1.0, 1.0)), f.x),
			f.y
		),
		f.z
	);
}

void fog() {
	vec3 wind_scroll = TIME * vec3(1.2, 0.1, 0.8);
	vec3 sample_pos = WORLD_POSITION * 0.16 + wind_scroll;

	// 2-octave 3D wind-scrolled billowing mist
	float n1 = noise3d(sample_pos);
	float n2 = noise3d(sample_pos * 2.15 - wind_scroll * 0.55);
	float noise = clamp(n1 * 0.65 + n2 * 0.35, 0.0, 1.0);

	// High-contrast billowing crests (0.085) and clear troughs (0.005)
	float contrast = pow(noise, 2.2);
	float density_wave = mix(trough_density, base_density, contrast);

	float h_atten = exp(-max(0.0, WORLD_POSITION.y - base_height) * height_falloff);
	float depth_boost = 1.0 + clamp((base_height - WORLD_POSITION.y) * 0.14, 0.0, 1.45);
	float edge_fade = smoothstep(0.0, 0.15, 0.5 - max(abs(UVW.x - 0.5), max(abs(UVW.y - 0.5), abs(UVW.z - 0.5))));

	DENSITY = density_wave * h_atten * depth_boost * edge_fade;
	ALBEDO = fog_albedo;
	EMISSION = fog_emission;
}
