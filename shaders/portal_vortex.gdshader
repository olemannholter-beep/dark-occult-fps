shader_type spatial;
render_mode unshaded, cull_disabled;

uniform vec4 portal_color_primary : source_color = vec4(1.0, 0.65, 0.28, 1.0);
uniform vec4 portal_color_secondary : source_color = vec4(0.35, 0.12, 0.04, 1.0);
uniform float vortex_speed : hint_range(0.1, 5.0) = 1.85;
uniform float spiral_tightness : hint_range(1.0, 20.0) = 9.5;
uniform float rim_power : hint_range(0.5, 6.0) = 2.4;
uniform float emission_boost : hint_range(0.5, 6.0) = 2.6;

void vertex() {
	// Subtle dimensional breathing displacement along vertex normal
	vec2 centered = UV * 2.0 - 1.0;
	float dist = length(centered);
	float wave = sin(dist * 8.0 - TIME * vortex_speed * 1.4) * 0.035 * clamp(1.0 - dist * 0.75, 0.0, 1.0);
	VERTEX += NORMAL * wave;
}

void fragment() {
	// Normalized elliptical coordinates centered at (0, 0)
	vec2 uv = (UV - vec2(0.5)) * 2.0;
	// Adjust slight arched portal aspect ratio near the top
	float radius = length(uv);
	float angle = atan(uv.y, uv.x);

	// Polar spiral coordinate warp driven by TIME * 1.85
	float t = TIME * vortex_speed;
	float spiral_a = angle + radius * spiral_tightness - t * 1.65;
	float spiral_b = angle * 3.0 - radius * (spiral_tightness * 1.35) + t * 1.15;

	float bands_primary = 0.5 + 0.5 * sin(spiral_a * 4.0 + sin(radius * 10.0 - t * 2.1) * 1.6);
	float bands_secondary = 0.5 + 0.5 * cos(spiral_b * 2.0 - cos(radius * 7.5 + t * 1.4) * 1.2);
	float ripple = 0.5 + 0.5 * sin(radius * 16.0 - t * 3.0 + bands_primary * 2.2);

	// Singularity core pull + glowing outer rim halo
	float core_singularity = smoothstep(0.32, 0.0, radius);
	float outer_rim = pow(clamp(radius, 0.0, 1.0), rim_power) * smoothstep(1.18, 0.78, radius);
	float arch_edge_mask = smoothstep(1.12, 0.88, radius);

	float swirl_mix = clamp(bands_primary * 0.55 + bands_secondary * 0.35 + ripple * 0.25, 0.0, 1.0);
	vec3 col = mix(portal_color_secondary.rgb * 0.25, portal_color_primary.rgb, swirl_mix);

	// Deep abyssal eye at the very center with intense bright inner event-horizon ring
	float event_horizon = smoothstep(0.42, 0.20, radius) * smoothstep(0.04, 0.18, radius);
	col = mix(col, portal_color_primary.rgb * 1.65, event_horizon * 0.85);
	col = mix(col, portal_color_secondary.rgb * 0.12, core_singularity * 0.82);

	// Emissive outer rim halo matching the stone arch frame
	col += portal_color_primary.rgb * outer_rim * 1.45;

	ALBEDO = col * emission_boost * max(arch_edge_mask, 0.35);
}
