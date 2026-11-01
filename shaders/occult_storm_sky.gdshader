shader_type sky;

uniform vec3 deep_sky_color : source_color = vec3(0.04, 0.03, 0.07);
uniform vec3 mid_sky_color : source_color = vec3(0.08, 0.05, 0.12);
uniform vec3 cloud_color : source_color = vec3(0.18, 0.05, 0.08);
uniform vec3 horizon_color : source_color = vec3(0.02, 0.02, 0.035);
uniform vec3 moon_color : source_color = vec3(0.96, 0.84, 0.78);
uniform vec3 moon_glow_color : source_color = vec3(0.78, 0.22, 0.14);
uniform vec3 moon_direction = vec3(0.12, 0.48, -0.87);
uniform float cloud_speed : hint_range(0.0, 0.1) = 0.016;
uniform float moon_size : hint_range(0.01, 0.15) = 0.065;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
	float v = 0.0;
	float a = 0.5;
	mat2 rot = mat2(vec2(0.8, -0.6), vec2(0.6, 0.8));
	for (int i = 0; i < 5; i++) {
		v += a * noise(p);
		p = rot * p * 2.02;
		a *= 0.5;
	}
	return v;
}

void sky() {
	vec3 dir = EYEDIR;
	float up = dir.y;

	// Seamless dark horizon blend
	float horizon_factor = clamp((up + 0.02) * 5.5, 0.0, 1.0);

	// Planar projection across the upper dome for churning storm clouds
	float dome_proj = max(up, 0.08) + 0.35;
	vec2 sky_coords = dir.xz / dome_proj;
	vec2 cloud_uv1 = sky_coords * 1.5 + vec2(TIME * cloud_speed * 0.7, TIME * cloud_speed);
	vec2 cloud_uv2 = sky_coords * 2.8 - vec2(TIME * cloud_speed * 1.1, TIME * cloud_speed * 0.4);

	float n1 = fbm(cloud_uv1);
	float n2 = fbm(cloud_uv2 + n1 * 0.65);
	float cloud_density = smoothstep(0.30, 0.76, n2) * smoothstep(-0.02, 0.25, up);

	// Looming Blood Moon aligned with DirectionalLight3D or fallback moon_direction
	vec3 m_dir = normalize(moon_direction);
	#if defined(LIGHT0_ENABLED)
	if (LIGHT0_ENABLED) {
		m_dir = LIGHT0_DIRECTION;
	}
	#endif

	float cos_angle = dot(dir, m_dir);
	float moon_threshold = 1.0 - moon_size * moon_size * 0.5;
	float moon_disc = smoothstep(moon_threshold, moon_threshold + 0.0012, cos_angle);

	// Multi-ring atmospheric blood moon corona
	float corona_inner = pow(max(cos_angle, 0.0), 42.0) * 1.15;
	float corona_outer = pow(max(cos_angle, 0.0), 8.5) * 0.45;
	float moon_corona = (corona_inner + corona_outer) * smoothstep(-0.02, 0.20, up);

	// Eldritch constellations / stars peeking through cloud gaps (smooth circular pinpricks)
	vec2 star_grid_coord = sky_coords * 70.0;
	vec2 star_cell = floor(star_grid_coord);
	vec2 star_sub = fract(star_grid_coord);
	float star_rand = hash21(star_cell);
	vec2 star_center = vec2(hash21(star_cell + vec2(1.2, 3.4)), hash21(star_cell + vec2(5.6, 7.8))) * 0.65 + 0.175;
	float star_dist = length(star_sub - star_center);
	float star_shape = smoothstep(0.075, 0.015, star_dist);
	float star_intensity = step(0.968, star_rand) * star_shape * max(up, 0.0) * (1.0 - cloud_density * 1.35);
	star_intensity = max(star_intensity, 0.0);

	// Base gradient: abyssal slate into deep bruise purple
	vec3 base_col = mix(deep_sky_color, mid_sky_color, clamp(up * 1.4, 0.0, 1.0));

	// Mix necrotic storm clouds
	vec3 sky_col = mix(base_col, cloud_color, cloud_density * 0.88);

	// Add faint starlight
	sky_col += vec3(0.75, 0.82, 1.0) * star_intensity * 2.2;

	// Add blood moon corona & disc
	sky_col += moon_glow_color * moon_corona * (1.0 - cloud_density * 0.65);
	sky_col = mix(sky_col, moon_color * 2.1, moon_disc * (1.0 - cloud_density * 0.55));

	// Blend with dark horizon fog
	sky_col = mix(horizon_color, sky_col, horizon_factor);

	COLOR = sky_col;
}
