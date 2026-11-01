shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform vec4 albedo_base : source_color = vec4(0.08, 0.11, 0.07, 1.0);
uniform vec4 albedo_tip : source_color = vec4(0.20, 0.18, 0.11, 1.0);
uniform float roughness : hint_range(0.0, 1.0) = 0.88;
uniform float wind_speed : hint_range(0.1, 8.0) = 2.6;
uniform float wind_strength : hint_range(0.0, 1.0) = 0.24;
uniform vec2 wind_direction = vec2(0.85, -0.52);

void vertex() {
	vec3 world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float height_factor = clamp((VERTEX.y - 0.04) / 0.52, 0.0, 1.0);
	float tip_weight = height_factor * height_factor;

	vec2 norm_wind = normalize(wind_direction);
	float wave1 = sin(TIME * wind_speed + world_pos.x * 0.38 + world_pos.z * 0.32);
	float wave2 = cos(TIME * wind_speed * 1.6 + world_pos.x * 0.75 - world_pos.z * 0.62) * 0.45;
	float gust = wave1 + wave2;

	VERTEX.x += norm_wind.x * gust * wind_strength * tip_weight;
	VERTEX.z += norm_wind.y * gust * wind_strength * tip_weight;
	VERTEX.y -= abs(gust) * wind_strength * 0.30 * tip_weight;

	// Slight normal adjustment for soft foliage shading
	NORMAL = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 0.45));
}

void fragment() {
	float height_grad = clamp(VERTEX.y / 0.58, 0.0, 1.0);
	vec3 col = mix(albedo_base.rgb, albedo_tip.rgb, height_grad);
	ALBEDO = col;
	ROUGHNESS = roughness;
	SPECULAR = 0.12;
}
