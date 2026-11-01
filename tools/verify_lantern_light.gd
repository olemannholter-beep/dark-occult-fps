extends SceneTree


func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("=== STARTING PLAYER LANTERN LIGHT RANGE & FALLOFF VERIFICATION ===")
	var level_ps: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_ps == null:
		push_error("Failed to load res://scenes/levels/town_overworld.tscn")
		quit(1)
		return

	var level_inst: Node3D = level_ps.instantiate() as Node3D
	root.add_child(level_inst)
	await process_frame

	var player: Node3D = level_inst.find_child("Player", true, false) as Node3D
	if player == null:
		push_error("Player node not found in town_overworld.tscn")
		quit(1)
		return

	var vm_ctrl: FPSViewmodelController = player.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	if vm_ctrl == null:
		push_error("ViewmodelRig (FPSViewmodelController) not found on Player")
		quit(1)
		return

	var l_light: OmniLight3D = vm_ctrl.lantern_light
	if l_light == null:
		l_light = player.find_child("LanternLight", true, false) as OmniLight3D

	if l_light == null:
		push_error("LanternLight (OmniLight3D) not found on Player")
		quit(1)
		return

	print(
		"  [Inspector Exports] lantern_base_range=%.1f | lantern_raised_range=%.1f | lantern_base_energy=%.2f | lantern_attenuation=%.2f" % [
			vm_ctrl.lantern_base_range,
			vm_ctrl.lantern_raised_range,
			vm_ctrl.lantern_base_energy,
			vm_ctrl.lantern_attenuation
		]
	)
	print(
		"  [LanternLight Base] omni_range=%.2f | omni_attenuation=%.2f | light_energy=%.2f | distance_fade_enabled=%s" % [
			l_light.omni_range,
			l_light.omni_attenuation,
			l_light.light_energy,
			str(l_light.distance_fade_enabled)
		]
	)

	var failures: int = 0
	if l_light.omni_range < 26.0:
		push_error("LanternLight omni_range is %.2f (expected >= 26.0)" % l_light.omni_range)
		failures += 1
	if l_light.omni_attenuation > 0.85:
		push_error("LanternLight omni_attenuation is %.2f (expected <= 0.85)" % l_light.omni_attenuation)
		failures += 1
	if l_light.distance_fade_enabled:
		push_error("LanternLight distance_fade_enabled should be false on player handheld lantern")
		failures += 1

	# Simulate holding RMB (_is_lantern_raised = true) for 1.0s and verify range lerps toward 34.0m
	vm_ctrl._is_lantern_raised = true
	for _i: int in range(60):
		vm_ctrl._update_lantern_raise(1.0 / 60.0)

	print(
		"  [LanternLight Raised] omni_range=%.2f | light_energy=%.2f" % [
			l_light.omni_range,
			l_light.light_energy
		]
	)
	if l_light.omni_range < 33.8:
		push_error("LanternLight raised omni_range is %.2f (expected ~34.0)" % l_light.omni_range)
		failures += 1

	level_inst.queue_free()
	await process_frame

	if failures > 0:
		push_error("verify_lantern_light.gd FAILED with %d error(s)" % failures)
		quit(1)
		return

	print("=== PLAYER LANTERN LIGHT VERIFICATION PASSED (0 ERRORS) ===")
	quit(0)
