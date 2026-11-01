class_name PlayerLoadoutManager
extends Node

signal loadout_changed
signal crafting_resources_changed
signal skill_unlocked(skill_id: String)
signal skills_respecced

@export var player_controller: FPSController
@export var viewmodel_controller: FPSViewmodelController
@export var hud: FPSHUD
@export var interaction_raycast: RayCast3D

var max_health: int = 100
var current_health: int = 100
var max_armor: int = 35
var current_armor: int = 35
var armor_tier_name: String = "Grave-Stalker's Boiled Leather"
var weapon_mod_name: String = "Sanctified Silver-Core"
var unlocked_weapons: Array[bool] = [true, false, false]
var unlocked_armors: Array[bool] = [true, false, false, false]
var unlocked_spells: Array[bool] = [true, false, false]
var unlocked_weapon_mods: Array[Array] = [
	[true, false, false, false],
	[true, false, false, false],
	[true, false, false, false]
]
var active_weapon_id: String = "revolver"
var damage_per_shot: float = 38.0
var reload_speed_mult: float = 1.0
var occult_blessing_level: int = 1
var lantern_radius_bonus: float = 0.0
var lantern_energy_bonus: float = 0.0
var occult_essence: int = 300

const ARMOR_SLOTS: Array[String] = ["HEAD", "CHEST", "HANDS", "LEGS", "FEET"]
const ARMOR_SLOT_WEIGHTS: Dictionary[String, float] = {
	"HEAD": 0.18,
	"CHEST": 0.34,
	"HANDS": 0.16,
	"LEGS": 0.18,
	"FEET": 0.14
}

var weapon_mod_index: int = 0
var weapon_mod_indices: Array[int] = [0, 0, 0]
var armor_tier_index: int = 0
var equipped_armor_index: int = 0
var equipped_spell_index: int = 0
var equipped_armor_slots: Dictionary = {
	"HEAD": 0,
	"CHEST": 0,
	"HANDS": 0,
	"LEGS": 0,
	"FEET": 0
}
var unlocked_armor_pieces: Dictionary = {
	"HEAD": [true, false, false, false],
	"CHEST": [true, false, false, false],
	"HANDS": [true, false, false, false],
	"LEGS": [true, false, false, false],
	"FEET": [true, false, false, false]
}

# RPG Leveling, 20-Node Celestial Astrolabe Skill Tree & 8 Biome Relics
var hunter_level: int = 1
var current_xp: int = 0
var xp_to_next_level: int = 100
var skill_points: int = 3
var spent_skill_points: int = 0
var unspent_attribute_points: int = 3
var unlocked_skills: Dictionary[String, bool] = {}

var bloodlust_rank: int = 1
var quicksilver_rank: int = 1
var ironclad_rank: int = 1
var eldritch_rank: int = 1

var move_speed_mult: float = 1.18
var fire_rate_mult: float = 1.0
var crit_damage_mult: float = 2.30
var firearm_damage_mult: float = 1.0
var dash_cooldown_mult: float = 0.85
var dash_iframe_duration: float = 0.18
var dash_max_charges: int = 1
var damage_reduction_ratio: float = 0.0
var knockback_resistance_ratio: float = 0.0
var orb_recovery_mult: float = 1.0
var lantern_reach_mult: float = 1.0
var soul_flame_recharge_mult: float = 1.0
var eldritch_damage_mult: float = 1.0
var eldritch_radius_bonus: float = 0.0
var ability_cooldown_mult: float = 1.0
var sanctuary_regen_per_sec: float = 0.0
var armor_regen_per_sec: float = 0.0

var active_relics: Array[int] = []
var active_relic_names: Array[String] = []
var equipped_relic_tiers: Dictionary[int, int] = {}
var equipped_relic_data: Array[Dictionary] = []
var _relic_dmg_bonus: float = 0.0
var _relic_reload_bonus: float = 0.0
var _relic_vit_bonus: float = 0.0
var _relic_soul_regen_bonus: float = 0.0

var crafting_resources: Dictionary[String, int] = {
	"silver": 35,
	"bone_ash": 15,
	"cursed_iron": 0,
	"soul_cores": 0
}

var _blood_frenzy_timer: float = 0.0
var _bloodlust_kill_stacks: int = 0
var _regen_accum: float = 0.0
var _armor_regen_accum: float = 0.0

var _base_move_speed: float = 5.5
var _base_weapon_damage: float = 38.0
var _consecration_damage_mult: float = 1.0
var _base_weapon_reload_mult: float = 1.0
var _base_armor_max: int = 35
var _base_armor_speed_mult: float = 1.18
var _sanctuary_hp_bonus: int = 0

var _focused_station: SanctuaryForgeStation = null
var _focused_portal: OccultPortal = null
var _focused_chest: ReliquaryChest = null

var _sfx_player_primary: AudioStreamPlayer = null
var _sfx_player_secondary: AudioStreamPlayer = null
var _sfx_weapon_mod: AudioStream = null
var _sfx_armor_equip: AudioStream = null
var _sfx_ui_armor_clank: AudioStream = null
var _sfx_ui_skill_chime: AudioStream = null
var _sfx_anvil_upgrade: AudioStream = null
var _sfx_sanctuary_heal: AudioStream = null
var _sfx_loot_pickup: AudioStream = null
var _sfx_level_up: AudioStream = null
var _sfx_player_hit: AudioStream = null
var _sfx_bell_resurrect: AudioStream = null


static func get_armor_set_catalog() -> Array[Dictionary]:
	return [
		{
			"index": 0,
			"name": "Grave-Stalker's Boiled Leather",
			"short_name": "GRAVE-STALKER LEATHER",
			"subtitle": "Agile Night-Watch Vambraces",
			"armor": 35,
			"rating_bars": 4,
			"speed_mult": 1.18,
			"dash_cd_mult": 0.85,
			"crit_bonus": 0.10,
			"reload_bonus": 0.0,
			"orb_bonus": 0.0,
			"fire_rate_bonus": 0.0,
			"dmg_reduction": 0.0,
			"knockback_res": 0.0,
			"vitality_bonus": 0,
			"spell_dmg_bonus": 0.0,
			"soul_recharge_bonus": 0.0,
			"lantern_radius_mult": 1.0,
			"perks": [
				"❖ 35 Base Armor  |  +18% Move & Dash Speed",
				"❖ -15% Quickstep Cooldown",
				"❖ +10% Weakpoint Critical Damage"
			],
			"accent_color": Color(0.92, 0.54, 0.28, 1.0)
		},
		{
			"index": 1,
			"name": "Inquisitor's Sanctified Brigandine",
			"short_name": "INQUISITOR BRIGANDINE",
			"subtitle": "Riveted Steel-and-Velvet Jack",
			"armor": 55,
			"rating_bars": 6,
			"speed_mult": 1.04,
			"dash_cd_mult": 1.0,
			"crit_bonus": 0.0,
			"reload_bonus": 0.18,
			"orb_bonus": 0.25,
			"fire_rate_bonus": 0.10,
			"dmg_reduction": 0.06,
			"knockback_res": 0.15,
			"vitality_bonus": 0,
			"spell_dmg_bonus": 0.0,
			"soul_recharge_bonus": 0.0,
			"lantern_radius_mult": 1.0,
			"perks": [
				"❖ 55 Base Armor  |  +18% Reload Velocity",
				"❖ +25% Blood & Armor Orb Recovery",
				"❖ +10% Firearm Attack Tempo"
			],
			"accent_color": Color(0.54, 0.82, 0.98, 1.0)
		},
		{
			"index": 2,
			"name": "Catacomb Juggernaut Fluted Plate",
			"short_name": "JUGGERNAUT FLUTED PLATE",
			"subtitle": "Heavy Gilded Siege Pauldrons",
			"armor": 90,
			"rating_bars": 10,
			"speed_mult": 0.96,
			"dash_cd_mult": 1.05,
			"crit_bonus": 0.0,
			"reload_bonus": 0.0,
			"orb_bonus": 0.0,
			"fire_rate_bonus": 0.0,
			"dmg_reduction": 0.22,
			"knockback_res": 0.50,
			"vitality_bonus": 20,
			"spell_dmg_bonus": 0.0,
			"soul_recharge_bonus": 0.0,
			"lantern_radius_mult": 1.0,
			"perks": [
				"❖ 90 Base Armor  |  -22% Incoming Damage",
				"❖ +50% Knockback Resistance",
				"❖ +20 Max Vitality HP"
			],
			"accent_color": Color(0.96, 0.78, 0.32, 1.0)
		},
		{
			"index": 3,
			"name": "Abyssal Reliquary Vestments",
			"short_name": "ABYSSAL RELIQUARY",
			"subtitle": "Bone-Caged Censer Gauntlets",
			"armor": 65,
			"rating_bars": 7,
			"speed_mult": 1.06,
			"dash_cd_mult": 0.95,
			"crit_bonus": 0.0,
			"reload_bonus": 0.0,
			"orb_bonus": 0.0,
			"fire_rate_bonus": 0.0,
			"dmg_reduction": 0.10,
			"knockback_res": 0.20,
			"vitality_bonus": 0,
			"spell_dmg_bonus": 0.35,
			"soul_recharge_bonus": 0.30,
			"lantern_radius_mult": 1.25,
			"perks": [
				"❖ 65 Base Armor  |  +35% Lantern Spell Damage",
				"❖ +30% Soul-Flame Recharge Velocity",
				"❖ +25% Handheld Lantern Illumination Reach"
			],
			"accent_color": Color(0.86, 0.38, 1.0, 1.0)
		}
	]


static func get_weapon_mod_catalog() -> Array[Dictionary]:
	return [
		{
			"index": 0,
			"name": "Sanctified Silver-Core",
			"short": "SILVER-CORE",
			"desc": "Balanced high stagger & +15% weakpoint crit multiplier.",
			"dmg_mult": 1.08,
			"reload_mult": 1.05,
			"recoil_mult": 0.95,
			"crit_add": 0.15,
			"color": Color(0.85, 0.92, 1.0, 1.0)
		},
		{
			"index": 1,
			"name": "Hellfire Incendiary Rite",
			"short": "HELLFIRE",
			"desc": "Ignites enemies for searing burn DoT & +24% firearm damage.",
			"dmg_mult": 1.24,
			"reload_mult": 1.00,
			"recoil_mult": 1.15,
			"crit_add": 0.05,
			"color": Color(1.0, 0.56, 0.16, 1.0)
		},
		{
			"index": 2,
			"name": "Ricochet Bone-Shrapnel",
			"short": "RICOCHET",
			"desc": "Rounds ricochet off stone surfaces once & deal bonus limb dismemberment.",
			"dmg_mult": 1.12,
			"reload_mult": 1.18,
			"recoil_mult": 0.88,
			"crit_add": 0.10,
			"color": Color(0.45, 0.88, 1.0, 1.0)
		},
		{
			"index": 3,
			"name": "Abyssal Blood-Leech Rite",
			"short": "BLOOD-LEECH",
			"desc": "Headshots & point-blank hits restore +4 HP and +5% Soul-Flame.",
			"dmg_mult": 1.15,
			"reload_mult": 1.10,
			"recoil_mult": 1.00,
			"crit_add": 0.12,
			"color": Color(0.96, 0.20, 0.28, 1.0)
		}
	]


static func get_lantern_spell_catalog() -> Array[Dictionary]:
	return [
		{
			"index": 0,
			"name": "Searing Pyre",
			"subtitle": "Solar-Amber Consecration",
			"desc": "Conical solar-amber fireblast that ignites enemies and melts armor plating.",
			"color": Color(1.0, 0.64, 0.20, 1.0)
		},
		{
			"index": 1,
			"name": "Shackles of the Penitent",
			"subtitle": "Iron-Chain Binding Rite",
			"desc": "Chains & immobilizes enemies in an arcane snare while amplifying crit damage taken.",
			"color": Color(0.46, 0.86, 1.0, 1.0)
		},
		{
			"index": 2,
			"name": "Aegis of the Reliquary",
			"subtitle": "Sanctified Ward Circle",
			"desc": "Sanctifies the ground, granting instant Armor barriers and repelling projectiles.",
			"color": Color(0.92, 0.34, 0.98, 1.0)
		}
	]


static func get_skill_node_ids() -> Array[String]:
	return [
		"blood_1", "blood_2", "blood_3", "blood_4",
		"quick_1", "quick_2", "quick_3", "quick_4",
		"iron_1", "iron_2", "iron_3", "iron_4",
		"eld_1", "eld_2", "eld_3", "eld_4",
		"syn_blood_quick", "syn_quick_iron", "syn_iron_eld", "syn_eld_blood"
	]


static func get_skill_tree_catalog() -> Dictionary[String, Dictionary]:
	var col_blood: Color = Color(0.95, 0.22, 0.20, 1.0)
	var col_quick: Color = Color(0.45, 0.88, 1.0, 1.0)
	var col_iron: Color = Color(0.95, 0.76, 0.32, 1.0)
	var col_eld: Color = Color(0.78, 0.38, 1.0, 1.0)

	return {
		# Constellation I — CRIMSON BLOODLUST (Column 0: x = 0.14)
		"blood_1": {
			"id": "blood_1",
			"title": "Serrated Rifling",
			"subtitle": "Constellation I — Crimson Bloodlust (Tier I)",
			"lore_quote": "\"Every groove carved inside the barrel is a prayer for arterial ruin.\"",
			"desc": "+15% Firearm Damage & +25% Ragdoll Dismemberment Impulse.",
			"cost": 1,
			"tier": 1,
			"constellation": 0,
			"prereqs": [] as Array[String],
			"branch_color": col_blood,
			"pos_uv": Vector2(0.14, 0.80),
			"stat_modifiers": {"firearm_dmg": 0.15}
		},
		"blood_2": {
			"id": "blood_2",
			"title": "Executioner's Tempo",
			"subtitle": "Constellation I — Crimson Bloodlust (Tier II)",
			"lore_quote": "\"The hammer falls in rhythm with the dying pulse of the catacombs.\"",
			"desc": "Killing an enemy instantly loads 1 round into your active weapon and grants +20% Fire Rate for 4.0s.",
			"cost": 1,
			"tier": 2,
			"constellation": 0,
			"prereqs": ["blood_1"] as Array[String],
			"branch_color": col_blood,
			"pos_uv": Vector2(0.14, 0.58),
			"stat_modifiers": {"fire_rate": 0.12}
		},
		"blood_3": {
			"id": "blood_3",
			"title": "Cruel Anatomy",
			"subtitle": "Constellation I — Crimson Bloodlust (Tier III)",
			"lore_quote": "\"Even bone-plated horrors harbor a fracture where silver may enter.\"",
			"desc": "+35% Weakpoint/Headshot Multiplier and bullets pierce through the first staggered or dying enemy.",
			"cost": 2,
			"tier": 3,
			"constellation": 0,
			"prereqs": ["blood_2"] as Array[String],
			"branch_color": col_blood,
			"pos_uv": Vector2(0.14, 0.36),
			"stat_modifiers": {"crit_mult": 0.35}
		},
		"blood_4": {
			"id": "blood_4",
			"title": "KEYSTONE: Reaper's Red Eucharist",
			"subtitle": "Constellation I — Grand Keystone (Tier IV)",
			"lore_quote": "\"In blood and black powder, the covenant of the Ossuary is sealed.\"",
			"desc": "Lethal kills trigger a 3.5m crimson bone-shrapnel nova (35 damage) and grant stacking +8% Bloodlust Damage (up to 5 stacks).",
			"cost": 3,
			"tier": 4,
			"constellation": 0,
			"prereqs": ["blood_3"] as Array[String],
			"branch_color": col_blood,
			"pos_uv": Vector2(0.14, 0.14),
			"stat_modifiers": {"firearm_dmg": 0.20, "crit_mult": 0.15}
		},

		# Constellation II — QUICKSILVER PHANTOM (Column 1: x = 0.38)
		"quick_1": {
			"id": "quick_1",
			"title": "Shadow-Step Greaves",
			"subtitle": "Constellation II — Quicksilver Phantom (Tier I)",
			"lore_quote": "\"Walk where the torchlight wavers; strike before the echo fades.\"",
			"desc": "+12% Sprint/Strafe Speed and -20% Hunter's Quickstep Dash Cooldown.",
			"cost": 1,
			"tier": 1,
			"constellation": 1,
			"prereqs": [] as Array[String],
			"branch_color": col_quick,
			"pos_uv": Vector2(0.38, 0.80),
			"stat_modifiers": {"move_speed": 0.12, "dash_cd": -0.20}
		},
		"quick_2": {
			"id": "quick_2",
			"title": "Sleight of the Gunsmith",
			"subtitle": "Constellation II — Quicksilver Phantom (Tier II)",
			"lore_quote": "\"Brass casings hit the flagstones only after the next cylinder is locked.\"",
			"desc": "+30% Reload Speed; performing a Quickstep Dash mid-reload automatically completes the current reload stage!",
			"cost": 1,
			"tier": 2,
			"constellation": 1,
			"prereqs": ["quick_1"] as Array[String],
			"branch_color": col_quick,
			"pos_uv": Vector2(0.38, 0.58),
			"stat_modifiers": {"reload_speed": 0.30}
		},
		"quick_3": {
			"id": "quick_3",
			"title": "Aerial Momentum",
			"subtitle": "Constellation II — Quicksilver Phantom (Tier III)",
			"lore_quote": "\"Gravity is merely another chain for the penitent to break.\"",
			"desc": "+25% Air-Dash & Jump Carry Momentum; firing while airborne or within 1.2s of a Quickstep deals +25% damage with 0 recoil spread penalty.",
			"cost": 2,
			"tier": 3,
			"constellation": 1,
			"prereqs": ["quick_2"] as Array[String],
			"branch_color": col_quick,
			"pos_uv": Vector2(0.38, 0.36),
			"stat_modifiers": {"move_speed": 0.08, "fire_rate": 0.15}
		},
		"quick_4": {
			"id": "quick_4",
			"title": "KEYSTONE: Phantom Phase-Walk",
			"subtitle": "Constellation II — Grand Keystone (Tier IV)",
			"lore_quote": "\"Between one heartbeat and the next, the hunter becomes mist.\"",
			"desc": "Quickstep Dash gains +1 extra charge (2 consecutive dashes before cooldown!), +50% longer i-frames (0.27s), and dashing through an enemy shock-stuns them for 1.5s.",
			"cost": 3,
			"tier": 4,
			"constellation": 1,
			"prereqs": ["quick_3"] as Array[String],
			"branch_color": col_quick,
			"pos_uv": Vector2(0.38, 0.14),
			"stat_modifiers": {"dash_iframes": 0.09, "dash_charges": 1.0}
		},

		# Constellation III — IRONCLAD BULWARK (Column 2: x = 0.62)
		"iron_1": {
			"id": "iron_1",
			"title": "Catacomb Plating",
			"subtitle": "Constellation III — Ironclad Bulwark (Tier I)",
			"lore_quote": "\"Forged from melted sanctuary bells and quenched in consecrated oil.\"",
			"desc": "+25 Max Vitality HP and +25 Max Armor Capacity.",
			"cost": 1,
			"tier": 1,
			"constellation": 2,
			"prereqs": [] as Array[String],
			"branch_color": col_iron,
			"pos_uv": Vector2(0.62, 0.80),
			"stat_modifiers": {"max_hp": 25.0, "max_armor": 25.0}
		},
		"iron_2": {
			"id": "iron_2",
			"title": "Sanctified Blood-Vials",
			"subtitle": "Constellation III — Ironclad Bulwark (Tier II)",
			"lore_quote": "\"What is spilled from the wicked shall mend the righteous.\"",
			"desc": "Health & Armor loot drops restore +40% more, and pickup vacuum radius is doubled (+100%).",
			"cost": 1,
			"tier": 2,
			"constellation": 2,
			"prereqs": ["iron_1"] as Array[String],
			"branch_color": col_iron,
			"pos_uv": Vector2(0.62, 0.58),
			"stat_modifiers": {"orb_recovery": 0.40, "max_hp": 10.0}
		},
		"iron_3": {
			"id": "iron_3",
			"title": "Unflinching Bastion",
			"subtitle": "Constellation III — Ironclad Bulwark (Tier III)",
			"lore_quote": "\"Let the mortar fall and the bone-cleaver ring; the tower does not bow.\"",
			"desc": "Reduces all incoming projectile and AoE mortar damage by 25% and grants immunity to camera-aim flinch while holding RMB (Lantern Raise).",
			"cost": 2,
			"tier": 3,
			"constellation": 2,
			"prereqs": ["iron_2"] as Array[String],
			"branch_color": col_iron,
			"pos_uv": Vector2(0.62, 0.36),
			"stat_modifiers": {"dmg_reduction": 0.25}
		},
		"iron_4": {
			"id": "iron_4",
			"title": "KEYSTONE: Immortal Reliquary Aegis",
			"subtitle": "Constellation III — Grand Keystone (Tier IV)",
			"lore_quote": "\"Sealed in gilt and martyr's bone, no abyssal claw may breach the ward.\"",
			"desc": "Passively regenerates +2.0 Armor per second in combat; dropping below 30% HP triggers an automatic Golden Aegis Shockwave that knocks back all nearby enemies and restores 40 Armor (15s cooldown).",
			"cost": 3,
			"tier": 4,
			"constellation": 2,
			"prereqs": ["iron_3"] as Array[String],
			"branch_color": col_iron,
			"pos_uv": Vector2(0.62, 0.14),
			"stat_modifiers": {"max_armor": 30.0, "dmg_reduction": 0.10}
		},

		# Constellation IV — ELDRITCH RELIQUARY (Column 3: x = 0.86)
		"eld_1": {
			"id": "eld_1",
			"title": "Astral Wick",
			"subtitle": "Constellation IV — Eldritch Reliquary (Tier I)",
			"lore_quote": "\"Fed by tallow rendered from ancient watchers, its light pierces the veil.\"",
			"desc": "+35% Handheld Lantern Illumination Range & +25% Lantern Spell ([F]) Recharge Rate.",
			"cost": 1,
			"tier": 1,
			"constellation": 3,
			"prereqs": [] as Array[String],
			"branch_color": col_eld,
			"pos_uv": Vector2(0.86, 0.80),
			"stat_modifiers": {"lantern_reach": 0.35, "soul_recharge": 0.25}
		},
		"eld_2": {
			"id": "eld_2",
			"title": "Withering Halo",
			"subtitle": "Constellation IV — Eldritch Reliquary (Tier II)",
			"lore_quote": "\"Where the sacred censer swings, the marrow of the undead turns to ash.\"",
			"desc": "Enemies inside your Lantern's inner light radius move 15% slower and take +18% bonus damage from all weapons.",
			"cost": 1,
			"tier": 2,
			"constellation": 3,
			"prereqs": ["eld_1"] as Array[String],
			"branch_color": col_eld,
			"pos_uv": Vector2(0.86, 0.58),
			"stat_modifiers": {"firearm_dmg": 0.10, "lantern_reach": 0.15}
		},
		"eld_3": {
			"id": "eld_3",
			"title": "Charnel Alchemy",
			"subtitle": "Constellation IV — Eldritch Reliquary (Tier III)",
			"lore_quote": "\"From rotting vessel to luminous ember, nothing is wasted in the rite.\"",
			"desc": "Dissolving enemy ragdolls release 2 seeking Soul-Embers that home in on the player to restore 12% Lantern Spell charge and 5 HP.",
			"cost": 2,
			"tier": 3,
			"constellation": 3,
			"prereqs": ["eld_2"] as Array[String],
			"branch_color": col_eld,
			"pos_uv": Vector2(0.86, 0.36),
			"stat_modifiers": {"soul_recharge": 0.30, "max_hp": 15.0}
		},
		"eld_4": {
			"id": "eld_4",
			"title": "KEYSTONE: Archon's Sovereign Pyre",
			"subtitle": "Constellation IV — Grand Keystone (Tier IV)",
			"lore_quote": "\"The lantern ceases to be a guide and becomes a furnace of judgment.\"",
			"desc": "[F] Lantern Spells gain +1 Max Charge, +50% AoE radius & damage, and leave consecrated ground that burns enemies for 5.0s.",
			"cost": 3,
			"tier": 4,
			"constellation": 3,
			"prereqs": ["eld_3"] as Array[String],
			"branch_color": col_eld,
			"pos_uv": Vector2(0.86, 0.14),
			"stat_modifiers": {"soul_recharge": 0.35, "lantern_reach": 0.25}
		},

		# 4 Cross-Constellation Hybrid Synergy Bridges (Tier 2.5, cost = 2 SP)
		"syn_blood_quick": {
			"id": "syn_blood_quick",
			"title": "SYNERGY: Crimson Mirage",
			"subtitle": "Hybrid Bridge — Bloodlust × Quicksilver",
			"lore_quote": "\"A phantom's step leaves a crimson bullet in its wake.\"",
			"desc": "Quickstep Dashing fires a free spectral ricochet bullet at the nearest enemy and grants +25% Crit Chance for 3.0s.",
			"cost": 2,
			"tier": 2,
			"constellation": 4,
			"prereqs": ["blood_2", "quick_2"] as Array[String],
			"branch_color": Color(0.95, 0.56, 0.64, 1.0),
			"pos_uv": Vector2(0.26, 0.47),
			"stat_modifiers": {"crit_mult": 0.25, "move_speed": 0.06}
		},
		"syn_quick_iron": {
			"id": "syn_quick_iron",
			"title": "SYNERGY: Battering Ram Step",
			"subtitle": "Hybrid Bridge — Quicksilver × Ironclad",
			"lore_quote": "\"Velocity wedded to fluted steel turns the hunter into a siege engine.\"",
			"desc": "Quickstep Dashing through or into an enemy deals 30 blunt stagger damage, sends them flying backward, and grants +15 Armor.",
			"cost": 2,
			"tier": 2,
			"constellation": 4,
			"prereqs": ["quick_2", "iron_2"] as Array[String],
			"branch_color": Color(0.76, 0.86, 0.62, 1.0),
			"pos_uv": Vector2(0.50, 0.47),
			"stat_modifiers": {"max_armor": 15.0, "move_speed": 0.05}
		},
		"syn_iron_eld": {
			"id": "syn_iron_eld",
			"title": "SYNERGY: Retaliatory Censer",
			"subtitle": "Hybrid Bridge — Ironclad × Eldritch",
			"lore_quote": "\"Strike the reliquary and the reliquary answers in solar fire.\"",
			"desc": "Whenever your Armor absorbs a hit, your Lantern automatically erupts with a free 4.5m Searing Pyre ring (3.0s internal cooldown).",
			"cost": 2,
			"tier": 2,
			"constellation": 4,
			"prereqs": ["iron_2", "eld_2"] as Array[String],
			"branch_color": Color(0.90, 0.60, 0.72, 1.0),
			"pos_uv": Vector2(0.74, 0.47),
			"stat_modifiers": {"dmg_reduction": 0.08, "soul_recharge": 0.18}
		},
		"syn_eld_blood": {
			"id": "syn_eld_blood",
			"title": "SYNERGY: Hex-Breaker Rounds",
			"subtitle": "Hybrid Bridge — Eldritch × Bloodlust",
			"lore_quote": "\"Where the astral flame marks the flesh, the silver bullet claims the soul.\"",
			"desc": "Firearms deal +30% bonus occult damage to enemies illuminated by your Lantern or afflicted by Lantern Spells.",
			"cost": 2,
			"tier": 2,
			"constellation": 4,
			"prereqs": ["eld_2", "blood_2"] as Array[String],
			"branch_color": Color(0.92, 0.34, 0.68, 1.0),
			"pos_uv": Vector2(0.50, 0.69),
			"stat_modifiers": {"firearm_dmg": 0.22, "lantern_reach": 0.15}
		}
	}


func _init() -> void:
	for sid: String in get_skill_node_ids():
		if not unlocked_skills.has(sid):
			unlocked_skills[sid] = false


func _ready() -> void:
	for sid: String in get_skill_node_ids():
		if not unlocked_skills.has(sid):
			unlocked_skills[sid] = false

	_ensure_interact_input_binding()
	_resolve_dependencies()
	_setup_audio_players()
	_recalculate_rpg_stats()
	current_health = max_health
	current_armor = max_armor
	_refresh_hud()


func _ensure_interact_input_binding() -> void:
	if not InputMap.has_action("interact"):
		InputMap.add_action("interact")
	var has_e: bool = false
	for ev: InputEvent in InputMap.action_get_events("interact"):
		if ev is InputEventKey:
			var kev: InputEventKey = ev as InputEventKey
			if kev.keycode == KEY_E or kev.physical_keycode == KEY_E:
				has_e = true
				break
	if not has_e:
		var e_key: InputEventKey = InputEventKey.new()
		e_key.keycode = KEY_E
		e_key.physical_keycode = KEY_E
		InputMap.action_add_event("interact", e_key)


func _resolve_dependencies() -> void:
	if player_controller == null:
		if get_parent() is FPSController:
			player_controller = get_parent() as FPSController
		elif owner is FPSController:
			player_controller = owner as FPSController

	if player_controller != null:
		if _base_move_speed <= 0.1:
			_base_move_speed = player_controller.move_speed

		if viewmodel_controller == null:
			viewmodel_controller = player_controller.find_child("ViewmodelRig", true, false) as FPSViewmodelController
		if hud == null:
			hud = player_controller.find_child("HUD", true, false) as FPSHUD
		if interaction_raycast == null:
			interaction_raycast = player_controller.find_child("InteractionRayCast3D", true, false) as RayCast3D
			if interaction_raycast == null:
				var cam: Camera3D = player_controller.find_child("Camera3D", true, false) as Camera3D
				if cam != null:
					interaction_raycast = RayCast3D.new()
					interaction_raycast.name = "InteractionRayCast3D"
					interaction_raycast.target_position = Vector3(0.0, 0.0, -3.5)
					interaction_raycast.collision_mask = 1
					interaction_raycast.collide_with_areas = true
					interaction_raycast.enabled = true
					cam.add_child(interaction_raycast)

	if viewmodel_controller != null:
		viewmodel_controller.loadout_manager = self

	if interaction_raycast != null and player_controller != null:
		interaction_raycast.target_position = Vector3(0.0, 0.0, -3.8)
		interaction_raycast.collision_mask = 1
		interaction_raycast.collide_with_areas = true
		interaction_raycast.enabled = true
		interaction_raycast.add_exception(player_controller)


func _setup_audio_players() -> void:
	_sfx_player_primary = AudioStreamPlayer.new()
	_sfx_player_primary.name = "HubSFXPrimary"
	_sfx_player_primary.volume_db = -2.0
	add_child(_sfx_player_primary)

	_sfx_player_secondary = AudioStreamPlayer.new()
	_sfx_player_secondary.name = "HubSFXSecondary"
	_sfx_player_secondary.volume_db = -3.5
	add_child(_sfx_player_secondary)

	if ResourceLoader.exists("res://assets/audio/sfx/hub_weapon_mod.wav"):
		_sfx_weapon_mod = load("res://assets/audio/sfx/hub_weapon_mod.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/hub_armor_equip.wav"):
		_sfx_armor_equip = load("res://assets/audio/sfx/hub_armor_equip.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ui_armor_equip_clank.wav"):
		_sfx_ui_armor_clank = load("res://assets/audio/sfx/ui_armor_equip_clank.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ui_skill_consecrate_chime.wav"):
		_sfx_ui_skill_chime = load("res://assets/audio/sfx/ui_skill_consecrate_chime.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/hub_anvil_upgrade.wav"):
		_sfx_anvil_upgrade = load("res://assets/audio/sfx/hub_anvil_upgrade.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/hub_sanctuary_heal.wav"):
		_sfx_sanctuary_heal = load("res://assets/audio/sfx/hub_sanctuary_heal.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/loot_pickup_chime.wav"):
		_sfx_loot_pickup = load("res://assets/audio/sfx/loot_pickup_chime.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/rpg_level_up_fanfare.wav"):
		_sfx_level_up = load("res://assets/audio/sfx/rpg_level_up_fanfare.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/player_hit_hurt.wav"):
		_sfx_player_hit = load("res://assets/audio/sfx/player_hit_hurt.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/enemy_sonic_bell_slam.wav"):
		_sfx_bell_resurrect = load("res://assets/audio/sfx/enemy_sonic_bell_slam.wav") as AudioStream


func _unhandled_input(_event: InputEvent) -> void:
	pass


func _process(delta: float) -> void:
	if player_controller == null or viewmodel_controller == null or hud == null or interaction_raycast == null:
		_resolve_dependencies()

	if _blood_frenzy_timer > 0.0:
		_blood_frenzy_timer = maxf(0.0, _blood_frenzy_timer - delta)
		if _blood_frenzy_timer <= 0.0:
			_recalculate_rpg_stats()

	if sanctuary_regen_per_sec > 0.0 and current_health < max_health:
		_regen_accum += sanctuary_regen_per_sec * delta
		if _regen_accum >= 1.0:
			var add_hp: int = int(floorf(_regen_accum))
			_regen_accum -= float(add_hp)
			current_health = mini(max_health, current_health + add_hp)
			_refresh_hud()

	if armor_regen_per_sec > 0.0 and current_armor < max_armor:
		_armor_regen_accum += armor_regen_per_sec * delta
		if _armor_regen_accum >= 1.0:
			var add_arm: int = int(floorf(_armor_regen_accum))
			_armor_regen_accum -= float(add_arm)
			current_armor = mini(max_armor, current_armor + add_arm)
			_refresh_hud()

	_update_interaction_focus()
	_handle_interaction_input()

	if Input.is_action_just_pressed("swap_weapon") and _focused_station == null:
		swap_weapon(1)

	if hud != null and viewmodel_controller != null:
		hud.update_spell_and_relics_display(
			viewmodel_controller.get_active_spell_name(),
			viewmodel_controller.ability_cooldown_remaining,
			active_relic_names,
			get_active_weapon_display_name()
		)


func _update_interaction_focus() -> void:
	_focused_station = null
	_focused_portal = null
	_focused_chest = null

	if hud != null and hud.character_menu != null and hud.character_menu.is_menu_open:
		hud.set_interaction_prompt("", false)
		return

	if interaction_raycast != null:
		interaction_raycast.force_raycast_update()
		if interaction_raycast.is_colliding():
			var collider: Object = interaction_raycast.get_collider()
			if collider is Node:
				_focused_station = _find_hub_station_from_node(collider as Node)
				if _focused_station == null:
					_focused_portal = _find_occult_portal_from_node(collider as Node)
				if _focused_station == null and _focused_portal == null:
					_focused_chest = _find_reliquary_chest_from_node(collider as Node)

	if hud != null:
		if _focused_station != null:
			hud.set_interaction_prompt(_focused_station.get_prompt_text(self), true)
		elif _focused_portal != null:
			hud.set_interaction_prompt(_focused_portal.get_prompt_text(self), true)
		elif _focused_chest != null:
			hud.set_interaction_prompt(_focused_chest.get_prompt_text(self), true)
		else:
			hud.set_interaction_prompt("", false)


func _find_hub_station_from_node(node: Node) -> SanctuaryForgeStation:
	var curr: Node = node
	while curr != null:
		if curr is SanctuaryForgeStation:
			return curr as SanctuaryForgeStation
		curr = curr.get_parent()
	return null


func _find_occult_portal_from_node(node: Node) -> OccultPortal:
	var curr: Node = node
	while curr != null:
		if curr is OccultPortal:
			return curr as OccultPortal
		curr = curr.get_parent()
	return null


func _find_reliquary_chest_from_node(node: Node) -> ReliquaryChest:
	var curr: Node = node
	while curr != null:
		if curr is ReliquaryChest:
			return curr as ReliquaryChest
		curr = curr.get_parent()
	return null


func _handle_interaction_input() -> void:
	if _focused_station != null:
		if Input.is_action_just_pressed("interact"):
			_focused_station.interact(self)
			if hud != null:
				hud.set_interaction_prompt(_focused_station.get_prompt_text(self), true)
		elif Input.is_action_just_pressed("cycle_option"):
			_focused_station.cycle_option(self)
			if hud != null:
				hud.set_interaction_prompt(_focused_station.get_prompt_text(self), true)
	elif _focused_portal != null:
		if Input.is_action_just_pressed("interact"):
			_focused_portal.interact(self)
			if hud != null:
				hud.set_interaction_prompt("", false)
	elif _focused_chest != null:
		if Input.is_action_just_pressed("interact"):
			_focused_chest.interact(self)
			if hud != null:
				hud.set_interaction_prompt(_focused_chest.get_prompt_text(self), true)


func get_active_weapon_display_name() -> String:
	match active_weapon_id:
		"shotgun":
			return "Hellfire Coach Gun"
		"stakedriver":
			return "Pneumatic Stake-Driver"
		_:
			return "Occult Revolver"


func get_weapon_slot_index(weapon_id: String) -> int:
	match weapon_id:
		"shotgun":
			return 1
		"stakedriver":
			return 2
		_:
			return 0


func get_weapon_id_from_slot(slot_idx: int) -> String:
	match posmod(slot_idx, 3):
		1:
			return "shotgun"
		2:
			return "stakedriver"
		_:
			return "revolver"


func _get_weapon_base_damage(weapon_id: String) -> float:
	match weapon_id:
		"shotgun":
			return 128.0
		"stakedriver":
			return 65.0
		_:
			return 38.0


func is_weapon_unlocked(weapon_idx_or_id: Variant) -> bool:
	var idx: int = 0
	if weapon_idx_or_id is int:
		idx = int(weapon_idx_or_id)
	elif weapon_idx_or_id is String:
		idx = get_weapon_slot_index(String(weapon_idx_or_id))
	else:
		idx = int(weapon_idx_or_id)
	if idx < 0 or idx >= unlocked_weapons.size():
		return false
	return bool(unlocked_weapons[idx])


func is_armor_unlocked(armor_idx: int) -> bool:
	if armor_idx < 0 or armor_idx >= unlocked_armors.size():
		return false
	return bool(unlocked_armors[armor_idx])


func get_equipped_armor_slot(slot_name: String) -> int:
	var s_key: String = slot_name.to_upper().strip_edges()
	if not ARMOR_SLOT_WEIGHTS.has(s_key):
		s_key = "CHEST"
	return posmod(int(equipped_armor_slots.get(s_key, equipped_armor_index)), 4)


func reset_for_new_run() -> void:
	unlocked_armors = [true, false, false, false]
	for slot_k: String in ARMOR_SLOTS:
		unlocked_armor_pieces[slot_k] = [true, false, false, false]
		equipped_armor_slots[slot_k] = 0
	armor_tier_index = 0
	equipped_armor_index = 0
	_recalculate_rpg_stats()
	current_health = max_health
	current_armor = max_armor
	_refresh_hud()
	loadout_changed.emit()


func get_unlocked_piece_count_for_set(set_idx: int) -> int:
	var clamped_set: int = posmod(set_idx, 4)
	var count: int = 0
	for slot_k: String in ARMOR_SLOTS:
		if is_armor_piece_unlocked(slot_k, clamped_set):
			count += 1
	return count


static func get_armor_piece_recipe(slot_name: String, set_idx: int) -> Dictionary:
	var s_key: String = slot_name.to_upper().strip_edges()
	var clamped_set: int = posmod(set_idx, 4)
	if clamped_set == 0:
		return {}
	match clamped_set:
		1:
			if s_key == "HANDS" or s_key == "FEET":
				return {"silver": 15, "bone_ash": 8}
			elif s_key == "HEAD" or s_key == "LEGS":
				return {"silver": 20, "bone_ash": 12, "cursed_iron": 1}
			else:
				return {"silver": 30, "bone_ash": 16, "cursed_iron": 1}
		2:
			if s_key == "HANDS" or s_key == "FEET":
				return {"silver": 30, "bone_ash": 10, "cursed_iron": 1}
			elif s_key == "HEAD" or s_key == "LEGS":
				return {"silver": 40, "bone_ash": 15, "cursed_iron": 2}
			else:
				return {"silver": 55, "bone_ash": 20, "cursed_iron": 3, "soul_cores": 1}
		_:
			if s_key == "HANDS" or s_key == "FEET":
				return {"silver": 45, "bone_ash": 15, "cursed_iron": 2, "soul_cores": 1}
			elif s_key == "HEAD" or s_key == "LEGS":
				return {"silver": 60, "bone_ash": 20, "cursed_iron": 2, "soul_cores": 1}
			else:
				return {"silver": 80, "bone_ash": 25, "cursed_iron": 3, "soul_cores": 2}


func craft_unlock_armor_piece(slot_name: String, set_idx: int) -> bool:
	var s_key: String = slot_name.to_upper().strip_edges()
	if not ARMOR_SLOT_WEIGHTS.has(s_key):
		return false
	var clamped_set: int = posmod(set_idx, 4)
	if is_armor_piece_unlocked(s_key, clamped_set):
		return false
	var recipe: Dictionary = get_armor_piece_recipe(s_key, clamped_set)
	if recipe.is_empty() or not spend_resources(recipe):
		return false
	unlock_armor_piece(s_key, clamped_set)
	if get_unlocked_piece_count_for_set(clamped_set) >= 5 and clamped_set >= 0 and clamped_set < unlocked_armors.size():
		unlocked_armors[clamped_set] = true
	equip_armor_slot(s_key, clamped_set)
	var p_info: Dictionary = get_armor_piece_info(s_key, clamped_set)
	var p_title: String = String(p_info.get("name", s_key))
	_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, _sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_anvil_upgrade)
	if hud != null:
		hud.show_rpg_banner(
			"VESTMENT PIECE FORGED & EQUIPPED: %s" % p_title.to_upper(),
			p_info.get("accent_color", Color(1.0, 0.84, 0.32, 1.0)) as Color,
			3.2
		)
	_refresh_hud()
	loadout_changed.emit()
	return true


func is_armor_piece_unlocked(slot_name: String, set_idx: int) -> bool:
	var clamped_set: int = posmod(set_idx, 4)
	var s_key: String = slot_name.to_upper().strip_edges()
	if unlocked_armor_pieces.has(s_key):
		var arr: Array = unlocked_armor_pieces[s_key] as Array
		if clamped_set >= 0 and clamped_set < arr.size():
			return bool(arr[clamped_set]) or is_armor_unlocked(clamped_set)
	return is_armor_unlocked(clamped_set) or clamped_set == 0


func unlock_armor_piece(slot_name: String, set_idx: int) -> void:
	var s_key: String = slot_name.to_upper().strip_edges()
	var clamped_set: int = posmod(set_idx, 4)
	if unlocked_armor_pieces.has(s_key):
		var arr: Array = unlocked_armor_pieces[s_key] as Array
		if clamped_set >= 0 and clamped_set < arr.size():
			arr[clamped_set] = true


func get_armor_piece_info(slot_name: String, set_idx: int) -> Dictionary:
	var s_key: String = slot_name.to_upper().strip_edges()
	if not ARMOR_SLOT_WEIGHTS.has(s_key):
		s_key = "CHEST"
	var clamped_set: int = posmod(set_idx, 4)
	var piece_names: Dictionary = {
		"HEAD": [
			"Grave-Stalker's Tricorn & Mask",
			"Inquisitor's Winged Sallet Helm",
			"Catacomb Juggernaut Siege Greathelm",
			"Abyssal Bone-Cage Crown"
		],
		"CHEST": [
			"Highwayman's Boiled Leather Greatcoat",
			"Inquisitor's Sanctified Brigandine Cuirass",
			"Catacomb Juggernaut Fluted Cuirass",
			"Abyssal Reliquary Mantle"
		],
		"HANDS": [
			"Boiled Leather Gauntlets",
			"Inquisitor's Riveted Gauntlets",
			"Catacomb Juggernaut Gauntlets",
			"Abyssal Censer Gauntlets"
		],
		"LEGS": [
			"Grave-Stalker's Buckled Breeches",
			"Inquisitor's Tasset Greaves",
			"Juggernaut Fluted Poleyn Greaves",
			"Abyssal Ritual Pillar Greaves"
		],
		"FEET": [
			"Shadow-Step Hunter Boots",
			"Inquisitor's Sanctified Sabatons",
			"Catacomb Ironclad Sabatons",
			"Abyssal Ash-Walker Treads"
		]
	}
	var set_cat: Array[Dictionary] = get_armor_set_catalog()
	var s_info: Dictionary = set_cat[clamped_set]
	var weight: float = ARMOR_SLOT_WEIGHTS.get(s_key, 0.20)
	var piece_armor: int = maxi(1, roundi(float(int(s_info["armor"])) * weight))
	var names_arr: Array = piece_names[s_key] as Array
	var piece_title: String = String(names_arr[clamped_set])
	var slot_passive: String = ""
	match clamped_set:
		0:
			slot_passive = "+%.1f%% Move Spd  |  -%.1f%% Dash CD  |  +%.1f%% Crit" % [
				(float(s_info["speed_mult"]) - 1.0) * 100.0 * weight,
				(1.0 - float(s_info["dash_cd_mult"])) * 100.0 * weight,
				float(s_info["crit_bonus"]) * 100.0 * weight
			]
		1:
			slot_passive = "+%.1f%% Reload  |  +%.1f%% Orb Rec  |  +%.1f%% Tempo" % [
				float(s_info["reload_bonus"]) * 100.0 * weight,
				float(s_info["orb_bonus"]) * 100.0 * weight,
				float(s_info["fire_rate_bonus"]) * 100.0 * weight
			]
		2:
			slot_passive = "-%.1f%% Dmg Taken  |  +%.0f%% Poise  |  +%d Max HP" % [
				float(s_info["dmg_reduction"]) * 100.0 * weight,
				float(s_info["knockback_res"]) * 100.0 * weight,
				maxi(1, roundi(float(int(s_info["vitality_bonus"])) * weight))
			]
		_:
			slot_passive = "+%.1f%% Spell Dmg  |  +%.1f%% Soul Reg  |  +%.1f%% Reach" % [
				float(s_info["spell_dmg_bonus"]) * 100.0 * weight,
				float(s_info["soul_recharge_bonus"]) * 100.0 * weight,
				(float(s_info["lantern_radius_mult"]) - 1.0) * 100.0 * weight
			]
	return {
		"name": piece_title,
		"slot": s_key,
		"set_index": clamped_set,
		"set_name": String(s_info["name"]),
		"armor": piece_armor,
		"weight": weight,
		"passive_bonus": slot_passive,
		"bonus_text": "+%d ARM  |  %s" % [piece_armor, slot_passive],
		"accent_color": s_info.get("accent_color", Color(0.9, 0.75, 0.35, 1.0))
	}


func get_active_armor_synergy(preview_armor_idx: int = -1) -> Dictionary:
	return get_active_armor_set_bonus_info(preview_armor_idx)


func get_active_armor_set_bonus_info(preview_armor_idx: int = -1) -> Dictionary:
	var counts: Array[int] = [0, 0, 0, 0]
	for slot_k: String in ARMOR_SLOTS:
		var s_idx: int = posmod(preview_armor_idx, 4) if preview_armor_idx >= 0 else posmod(int(equipped_armor_slots.get(slot_k, equipped_armor_index)), 4)
		counts[s_idx] += 1
	var best_set: int = 0
	var max_cnt: int = 0
	for i: int in range(4):
		if counts[i] > max_cnt:
			max_cnt = counts[i]
			best_set = i
	var bonus_mult: float = 1.0
	if max_cnt >= 5:
		bonus_mult = 1.25
	elif max_cnt >= 3:
		bonus_mult = 1.10
	return {
		"max_matching_count": max_cnt,
		"matching_count": max_cnt,
		"dominant_set_index": best_set,
		"bonus_mult": bonus_mult,
		"bonus_pct": roundi((bonus_mult - 1.0) * 100.0)
	}


func _compute_combined_armor_stats(preview_armor_idx: int = -1) -> Dictionary[String, float]:
	var armors: Array[Dictionary] = get_armor_set_catalog()
	var total_armor: float = 0.0
	var speed_delta: float = 0.0
	var dash_cd_delta: float = 0.0
	var crit_bonus: float = 0.0
	var reload_bonus: float = 0.0
	var orb_bonus: float = 0.0
	var fire_rate_bonus: float = 0.0
	var dmg_reduction: float = 0.0
	var knockback_res: float = 0.0
	var vitality_bonus: float = 0.0
	var spell_dmg_bonus: float = 0.0
	var soul_recharge_bonus: float = 0.0
	var lantern_rad_delta: float = 0.0

	for slot_k: String in ARMOR_SLOTS:
		var w: float = ARMOR_SLOT_WEIGHTS.get(slot_k, 0.20)
		var s_idx: int = posmod(preview_armor_idx, 4) if preview_armor_idx >= 0 else posmod(int(equipped_armor_slots.get(slot_k, equipped_armor_index)), 4)
		var a_info: Dictionary = armors[s_idx]
		total_armor += float(int(a_info["armor"])) * w
		speed_delta += (float(a_info["speed_mult"]) - 1.0) * w
		dash_cd_delta += (float(a_info["dash_cd_mult"]) - 1.0) * w
		crit_bonus += float(a_info["crit_bonus"]) * w
		reload_bonus += float(a_info["reload_bonus"]) * w
		orb_bonus += float(a_info["orb_bonus"]) * w
		fire_rate_bonus += float(a_info["fire_rate_bonus"]) * w
		dmg_reduction += float(a_info["dmg_reduction"]) * w
		knockback_res += float(a_info["knockback_res"]) * w
		vitality_bonus += float(int(a_info["vitality_bonus"])) * w
		spell_dmg_bonus += float(a_info["spell_dmg_bonus"]) * w
		soul_recharge_bonus += float(a_info["soul_recharge_bonus"]) * w
		lantern_rad_delta += (float(a_info["lantern_radius_mult"]) - 1.0) * w

	var set_bonus_info: Dictionary = get_active_armor_set_bonus_info(preview_armor_idx)
	var b_mult: float = float(set_bonus_info["bonus_mult"])

	return {
		"armor": roundf(total_armor * b_mult),
		"speed_mult": 1.0 + speed_delta * b_mult,
		"dash_cd_mult": 1.0 + dash_cd_delta,
		"crit_bonus": crit_bonus * b_mult,
		"reload_bonus": reload_bonus * b_mult,
		"orb_bonus": orb_bonus * b_mult,
		"fire_rate_bonus": fire_rate_bonus * b_mult,
		"dmg_reduction": dmg_reduction * b_mult,
		"knockback_res": knockback_res * b_mult,
		"vitality_bonus": roundf(vitality_bonus * b_mult),
		"spell_dmg_bonus": spell_dmg_bonus * b_mult,
		"soul_recharge_bonus": soul_recharge_bonus * b_mult,
		"lantern_radius_mult": 1.0 + lantern_rad_delta * b_mult
	}


func is_spell_unlocked(spell_idx: int) -> bool:
	if spell_idx < 0 or spell_idx >= unlocked_spells.size():
		return false
	return bool(unlocked_spells[spell_idx])


func is_weapon_mod_unlocked(weapon_idx: int, mod_idx: int) -> bool:
	if weapon_idx < 0 or weapon_idx >= unlocked_weapon_mods.size():
		return false
	var w_mods: Array = unlocked_weapon_mods[weapon_idx] as Array
	if mod_idx < 0 or mod_idx >= w_mods.size():
		return false
	return bool(w_mods[mod_idx])


func notify_locked_forge_required() -> void:
	_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, null)
	if hud != null:
		hud.show_rpg_banner(
			"[ FORGE REQUIRED : CRAFT AT THE CHURCH SANCTUARY ANVIL ]",
			Color(1.0, 0.58, 0.22, 1.0),
			2.4
		)


func swap_weapon(step: int = 1) -> void:
	if unlocked_weapons.is_empty():
		return
	var curr_idx: int = get_weapon_slot_index(active_weapon_id)
	var dir_step: int = 1 if step >= 0 else -1
	for i: int in range(1, 4):
		var cand_idx: int = posmod(curr_idx + dir_step * i, 3)
		if is_weapon_unlocked(cand_idx):
			if cand_idx != curr_idx:
				equip_weapon(cand_idx)
			else:
				notify_locked_forge_required()
			return


func equip_weapon(weapon_target: Variant) -> bool:
	var slot_idx: int = 0
	var weapon_id: String = "revolver"
	if weapon_target is int:
		slot_idx = posmod(int(weapon_target), 3)
		weapon_id = get_weapon_id_from_slot(slot_idx)
	else:
		weapon_id = String(weapon_target)
		slot_idx = get_weapon_slot_index(weapon_id)

	if not is_weapon_unlocked(slot_idx):
		notify_locked_forge_required()
		return false

	active_weapon_id = weapon_id
	weapon_mod_index = weapon_mod_indices[slot_idx]
	_sync_active_weapon_mod_properties()
	_recalculate_rpg_stats()
	if viewmodel_controller != null:
		viewmodel_controller.switch_active_weapon(active_weapon_id)
	_refresh_hud()
	loadout_changed.emit()
	return true


func equip_weapon_mod(weapon_slot_idx: int, mod_idx: int) -> bool:
	var w_idx: int = posmod(weapon_slot_idx, 3)
	var m_idx: int = posmod(mod_idx, 4)
	if not is_weapon_unlocked(w_idx) or not is_weapon_mod_unlocked(w_idx, m_idx):
		notify_locked_forge_required()
		return false

	weapon_mod_indices[w_idx] = m_idx

	var target_weapon_id: String = get_weapon_id_from_slot(w_idx)
	if active_weapon_id != target_weapon_id:
		active_weapon_id = target_weapon_id
		if viewmodel_controller != null:
			viewmodel_controller.switch_active_weapon(active_weapon_id)

	weapon_mod_index = m_idx
	var rec_mult: float = _sync_active_weapon_mod_properties()
	_recalculate_rpg_stats()

	if viewmodel_controller != null:
		var mods: Array[Dictionary] = get_weapon_mod_catalog()
		var rune_col: Color = mods[m_idx]["color"] as Color
		viewmodel_controller.apply_weapon_consecration(rune_col, reload_speed_mult, rec_mult)

	_play_sfx(_sfx_weapon_mod, null)
	_refresh_hud()
	loadout_changed.emit()
	return true


func _sync_active_weapon_mod_properties() -> float:
	var slot_idx: int = get_weapon_slot_index(active_weapon_id)
	var m_idx: int = posmod(weapon_mod_indices[slot_idx], 4)
	weapon_mod_index = m_idx
	var mods: Array[Dictionary] = get_weapon_mod_catalog()
	var mod_info: Dictionary = mods[m_idx]
	weapon_mod_name = String(mod_info["name"])
	_consecration_damage_mult = float(mod_info["dmg_mult"])
	_base_weapon_reload_mult = float(mod_info["reload_mult"])
	return float(mod_info["recoil_mult"])


func equip_lantern_spell(spell_idx: int) -> bool:
	var s_idx: int = posmod(spell_idx, 3)
	if not is_spell_unlocked(s_idx):
		notify_locked_forge_required()
		return false
	equipped_spell_index = s_idx
	if viewmodel_controller != null:
		viewmodel_controller.active_spell_index = equipped_spell_index
		viewmodel_controller.spell_cast.emit(equipped_spell_index, viewmodel_controller.get_active_spell_name())
	_play_sfx(_sfx_weapon_mod, null)
	_refresh_hud()
	loadout_changed.emit()
	return true


func equip_spell(spell_idx: int) -> bool:
	return equip_lantern_spell(spell_idx)


func is_skill_unlocked(skill_id: String) -> bool:
	return bool(unlocked_skills.get(skill_id, false))


func are_skill_prereqs_met(skill_id: String) -> bool:
	var catalog: Dictionary[String, Dictionary] = get_skill_tree_catalog()
	if not catalog.has(skill_id):
		return false
	var node_info: Dictionary = catalog[skill_id]
	var prereqs: Array = node_info.get("prereqs", []) as Array
	for pre_var: Variant in prereqs:
		var pre_id: String = String(pre_var)
		if not is_skill_unlocked(pre_id):
			return false
	return true


func can_unlock_skill(skill_id: String) -> bool:
	if is_skill_unlocked(skill_id):
		return false
	var catalog: Dictionary[String, Dictionary] = get_skill_tree_catalog()
	if not catalog.has(skill_id):
		return false
	var cost: int = int(catalog[skill_id].get("cost", 1))
	if skill_points < cost:
		return false
	return are_skill_prereqs_met(skill_id)


func unlock_skill(skill_id: String) -> bool:
	if not can_unlock_skill(skill_id):
		return false
	var catalog: Dictionary[String, Dictionary] = get_skill_tree_catalog()
	var node_info: Dictionary = catalog[skill_id]
	var cost: int = int(node_info.get("cost", 1))

	skill_points -= cost
	spent_skill_points += cost
	unspent_attribute_points = skill_points
	unlocked_skills[skill_id] = true

	var const_idx: int = int(node_info.get("constellation", 0))
	match const_idx:
		0:
			bloodlust_rank += 1
		1:
			quicksilver_rank += 1
		2:
			ironclad_rank += 1
		3:
			eldritch_rank += 1
		_:
			bloodlust_rank += 1
			quicksilver_rank += 1

	_recalculate_rpg_stats()
	_play_sfx(_sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_anvil_upgrade, null)
	if hud != null:
		hud.show_rpg_banner(
			"RITE CONSECRATED: %s" % String(node_info.get("title", skill_id)).to_upper(),
			node_info.get("branch_color", Color(1.0, 0.84, 0.32, 1.0)) as Color,
			2.8
		)
	_refresh_hud()
	skill_unlocked.emit(skill_id)
	loadout_changed.emit()
	return true


func respec_all_skills() -> int:
	var refunded: int = spent_skill_points
	if refunded <= 0:
		# Also check any unlocked skills in case unlocked directly
		var catalog: Dictionary[String, Dictionary] = get_skill_tree_catalog()
		for sid: String in unlocked_skills.keys():
			if bool(unlocked_skills[sid]) and catalog.has(sid):
				refunded += int(catalog[sid].get("cost", 1))
	for sid: String in get_skill_node_ids():
		unlocked_skills[sid] = false

	skill_points += refunded
	spent_skill_points = 0
	unspent_attribute_points = skill_points
	bloodlust_rank = 1
	quicksilver_rank = 1
	ironclad_rank = 1
	eldritch_rank = 1

	_recalculate_rpg_stats()
	_play_sfx(_sfx_sanctuary_heal, _sfx_ui_skill_chime)
	if hud != null:
		hud.show_rpg_banner(
			"RITE OF ABSOLUTION — %d SOUL POINTS REFUNDED" % refunded,
			Color(1.0, 0.84, 0.36, 1.0),
			2.8
		)
	_refresh_hud()
	skills_respecced.emit()
	loadout_changed.emit()
	return refunded


func grant_sanctuary_blessing_sp(amount: int = 2) -> void:
	if amount <= 0:
		return
	skill_points += amount
	unspent_attribute_points = skill_points
	_play_sfx(_sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_sanctuary_heal, null)
	if hud != null:
		hud.show_rpg_banner(
			"SANCTUARY BLESSING BESTOWED: +%d RITE POINTS" % amount,
			Color(1.0, 0.88, 0.36, 1.0),
			2.5
		)
	_refresh_hud()
	loadout_changed.emit()


func get_unlocked_skills_count() -> int:
	var count: int = 0
	for sid: String in unlocked_skills.keys():
		if bool(unlocked_skills[sid]):
			count += 1
	return count


func compute_stat_ledger(preview_armor_idx: int = -1, preview_skill_id: String = "") -> Dictionary[String, float]:
	var arm_info: Dictionary[String, float] = _compute_combined_armor_stats(preview_armor_idx)

	var mods: Array[Dictionary] = get_weapon_mod_catalog()
	var slot_idx: int = get_weapon_slot_index(active_weapon_id)
	var mod_info: Dictionary = mods[posmod(weapon_mod_indices[slot_idx], 4)]

	var bl_steps: int = maxi(0, bloodlust_rank - 1)
	var qs_steps: int = maxi(0, quicksilver_rank - 1)
	var ic_steps: int = maxi(0, ironclad_rank - 1)
	var ef_steps: int = maxi(0, eldritch_rank - 1)

	var dmg_mult: float = float(mod_info["dmg_mult"]) * (1.0 + float(bl_steps) * 0.04)
	var crit_mult: float = 2.10 + float(arm_info["crit_bonus"]) + float(mod_info["crit_add"]) + float(bl_steps) * 0.04
	var atk_tempo: float = 1.0 + float(arm_info["fire_rate_bonus"]) + float(qs_steps) * 0.03
	var reload_vel: float = float(mod_info["reload_mult"]) * (1.0 + float(arm_info["reload_bonus"]) + float(qs_steps) * 0.04)
	var qstep_spd: float = float(arm_info["speed_mult"]) * (1.0 + float(qs_steps) * 0.02)
	var qstep_cd: float = float(arm_info["dash_cd_mult"])
	var qstep_iframes: float = 0.18
	var max_vit: float = float(100 + _sanctuary_hp_bonus + roundi(arm_info["vitality_bonus"]) + ic_steps * 10)
	var max_arm: float = float(roundi(arm_info["armor"]) + ic_steps * 8 + (40 if has_relic(4) else 0))
	var dmg_res: float = float(arm_info["dmg_reduction"])
	var lantern_reach: float = float(arm_info["lantern_radius_mult"]) + (lantern_radius_bonus / 26.0)
	var soul_recharge: float = 1.0 + float(arm_info["soul_recharge_bonus"]) + float(ef_steps) * 0.05
	var unlocked_cnt: float = float(get_unlocked_skills_count())

	if _blood_frenzy_timer > 0.0:
		atk_tempo += 0.20
		qstep_spd += 0.10
	if has_relic(1):
		crit_mult += 0.25
	if has_relic(2):
		reload_vel += 0.20
	if has_relic(3):
		soul_recharge += 0.30

	dmg_mult += _relic_dmg_bonus
	reload_vel += _relic_reload_bonus
	max_vit += _relic_vit_bonus
	soul_recharge += _relic_soul_regen_bonus

	var catalog: Dictionary[String, Dictionary] = get_skill_tree_catalog()
	for sid: String in get_skill_node_ids():
		var active: bool = is_skill_unlocked(sid) or (sid == preview_skill_id and not is_skill_unlocked(sid))
		if not active or not catalog.has(sid):
			continue
		if sid == preview_skill_id and not is_skill_unlocked(sid):
			unlocked_cnt += 1.0
		var smods: Dictionary = catalog[sid].get("stat_modifiers", {}) as Dictionary
		dmg_mult += float(smods.get("firearm_dmg", 0.0))
		crit_mult += float(smods.get("crit_mult", 0.0))
		atk_tempo += float(smods.get("fire_rate", 0.0))
		reload_vel += float(smods.get("reload_speed", 0.0))
		qstep_spd += float(smods.get("move_speed", 0.0))
		qstep_cd += float(smods.get("dash_cd", 0.0))
		qstep_iframes += float(smods.get("dash_iframes", 0.0))
		max_vit += float(smods.get("max_hp", 0.0))
		max_arm += float(smods.get("max_armor", 0.0))
		dmg_res += float(smods.get("dmg_reduction", 0.0))
		lantern_reach += float(smods.get("lantern_reach", 0.0))
		soul_recharge += float(smods.get("soul_recharge", 0.0))

	dmg_res = clampf(dmg_res, 0.0, 0.75)
	qstep_cd = clampf(qstep_cd, 0.40, 1.50)

	return {
		"firearm_damage_pct": dmg_mult * 100.0,
		"crit_multiplier_pct": crit_mult * 100.0,
		"attack_tempo_pct": atk_tempo * 100.0,
		"reload_velocity_pct": reload_vel * 100.0,
		"quickstep_speed_pct": qstep_spd * 100.0,
		"quickstep_iframes_ms": qstep_iframes * 1000.0,
		"max_vitality": max_vit,
		"max_armor": max_arm,
		"damage_resistance_pct": dmg_res * 100.0,
		"lantern_reach_m": 26.0 * lantern_reach,
		"soul_flame_recharge_pct": soul_recharge * 100.0,
		"unlocked_rites_count": unlocked_cnt
	}


func _recalculate_stats() -> void:
	_recalculate_rpg_stats()


func _recalculate_rpg_stats() -> void:
	var armors: Array[Dictionary] = get_armor_set_catalog()
	var syn_info: Dictionary = get_active_armor_set_bonus_info(-1)
	var dom_idx: int = posmod(int(syn_info.get("dominant_set_index", equipped_armor_index)), 4)
	var set_info: Dictionary = armors[dom_idx]
	armor_tier_name = String(set_info["name"])
	var arm_info: Dictionary[String, float] = _compute_combined_armor_stats(-1)
	_base_armor_max = roundi(arm_info["armor"])
	_base_armor_speed_mult = float(arm_info["speed_mult"])

	_sync_active_weapon_mod_properties()
	var ledger: Dictionary[String, float] = compute_stat_ledger(-1, "")

	firearm_damage_mult = ledger["firearm_damage_pct"] / 100.0
	_base_weapon_damage = _get_weapon_base_damage(active_weapon_id)
	damage_per_shot = roundf(_base_weapon_damage * firearm_damage_mult)
	crit_damage_mult = ledger["crit_multiplier_pct"] / 100.0
	fire_rate_mult = ledger["attack_tempo_pct"] / 100.0
	reload_speed_mult = ledger["reload_velocity_pct"] / 100.0
	move_speed_mult = ledger["quickstep_speed_pct"] / 100.0
	dash_iframe_duration = ledger["quickstep_iframes_ms"] / 1000.0
	dash_max_charges = 2 if is_skill_unlocked("quick_4") else 1
	damage_reduction_ratio = ledger["damage_resistance_pct"] / 100.0
	knockback_resistance_ratio = float(arm_info["knockback_res"])
	orb_recovery_mult = 1.0 + float(arm_info["orb_bonus"]) + (0.40 if is_skill_unlocked("iron_2") else 0.0)
	lantern_reach_mult = ledger["lantern_reach_m"] / 26.0
	soul_flame_recharge_mult = ledger["soul_flame_recharge_pct"] / 100.0

	if player_controller != null:
		player_controller.move_speed = _base_move_speed * move_speed_mult

	if viewmodel_controller != null:
		viewmodel_controller.reload_speed_mult = reload_speed_mult
		viewmodel_controller.lantern_range_bonus = maxf(0.0, ledger["lantern_reach_m"] - 26.0)

	var prev_max_hp: int = max_health
	var prev_max_armor: int = max_armor
	max_health = roundi(ledger["max_vitality"])
	max_armor = roundi(ledger["max_armor"])
	sanctuary_regen_per_sec = float(maxi(0, ironclad_rank - 1)) * 1.5
	armor_regen_per_sec = 2.0 if is_skill_unlocked("iron_4") else 0.0

	if max_health > prev_max_hp:
		current_health += (max_health - prev_max_hp)
	current_health = clampi(current_health, 0, max_health)

	if max_armor > prev_max_armor:
		current_armor += (max_armor - prev_max_armor)
	current_armor = clampi(current_armor, 0, max_armor)

	eldritch_damage_mult = 1.0 + float(arm_info["spell_dmg_bonus"]) + (0.50 if is_skill_unlocked("eld_4") else 0.0)
	if has_relic(3):
		eldritch_damage_mult *= 1.35
	eldritch_radius_bonus = (2.5 if is_skill_unlocked("eld_4") else 0.0) + float(maxi(0, eldritch_rank - 1)) * 0.8
	ability_cooldown_mult = clampf(1.0 / maxf(0.35, soul_flame_recharge_mult), 0.25, 1.0)


func add_xp(amount: int) -> void:
	if amount <= 0:
		return
	current_xp += amount
	var leveled_up: bool = false

	while current_xp >= xp_to_next_level:
		current_xp -= xp_to_next_level
		hunter_level += 1
		skill_points += 2
		unspent_attribute_points = skill_points
		xp_to_next_level = roundi(float(xp_to_next_level) * 1.35)
		leveled_up = true

	if leveled_up:
		_recalculate_rpg_stats()
		current_health = max_health
		current_armor = max_armor
		_play_sfx(_sfx_level_up, _sfx_sanctuary_heal)
		if hud != null:
			hud.show_rpg_banner(
				"HUNTER LEVEL UP! Level %d — +2 Rite Points" % hunter_level,
				Color(1.0, 0.86, 0.30, 1.0),
				3.6
			)
	_refresh_hud()
	loadout_changed.emit()


func spend_attribute_point(attr_id: int) -> bool:
	# Map quick-keys [1..4] to the next available skill in Constellation 0..3 or fallback rank upgrade
	var const_prefixes: Array[String] = ["blood_", "quick_", "iron_", "eld_"]
	if attr_id >= 1 and attr_id <= 4:
		var prefix: String = const_prefixes[attr_id - 1]
		for tier_i: int in range(1, 5):
			var candidate_id: String = "%s%d" % [prefix, tier_i]
			if can_unlock_skill(candidate_id):
				return unlock_skill(candidate_id)

	if skill_points <= 0:
		return false

	var attr_name: String = ""
	match attr_id:
		1:
			if bloodlust_rank >= 10:
				return false
			bloodlust_rank += 1
			attr_name = "Bloodlust (Rank %d)" % bloodlust_rank
		2:
			if quicksilver_rank >= 10:
				return false
			quicksilver_rank += 1
			attr_name = "Quicksilver (Rank %d)" % quicksilver_rank
		3:
			if ironclad_rank >= 10:
				return false
			ironclad_rank += 1
			attr_name = "Ironclad (Rank %d)" % ironclad_rank
		4:
			if eldritch_rank >= 10:
				return false
			eldritch_rank += 1
			attr_name = "Eldritch Focus (Rank %d)" % eldritch_rank
		_:
			return false

	skill_points -= 1
	spent_skill_points += 1
	unspent_attribute_points = skill_points
	_recalculate_rpg_stats()
	_play_sfx(_sfx_anvil_upgrade, null)
	if hud != null:
		hud.show_rpg_banner(
			"ATTRIBUTE UPGRADED: %s" % attr_name,
			Color(1.0, 0.82, 0.36, 1.0),
			2.4
		)
	_refresh_hud()
	loadout_changed.emit()
	return true


func has_relic(relic_id: int) -> bool:
	return active_relics.has(relic_id)


func get_resource_amount(res_key: String) -> int:
	return int(crafting_resources.get(res_key, 0))


func add_resource(res_key: String, amount: int) -> void:
	if amount <= 0:
		return
	if not crafting_resources.has(res_key):
		crafting_resources[res_key] = 0
	crafting_resources[res_key] = int(crafting_resources[res_key]) + amount
	if res_key == "silver":
		occult_essence += amount
	_refresh_hud()
	crafting_resources_changed.emit()
	loadout_changed.emit()


func can_afford(cost_dict: Dictionary) -> bool:
	for k_var: Variant in cost_dict.keys():
		var res_key: String = String(k_var)
		var req: int = int(cost_dict[k_var])
		if req > 0 and get_resource_amount(res_key) < req:
			return false
	return true


func spend_resources(cost_dict: Dictionary) -> bool:
	if not can_afford(cost_dict):
		return false
	for k_var: Variant in cost_dict.keys():
		var res_key: String = String(k_var)
		var req: int = int(cost_dict[k_var])
		if req > 0:
			crafting_resources[res_key] = maxi(0, get_resource_amount(res_key) - req)
	_refresh_hud()
	crafting_resources_changed.emit()
	loadout_changed.emit()
	return true


static func get_item_recipe(category: String, index: int) -> Dictionary:
	var cat_norm: String = category.to_lower().strip_edges()
	match cat_norm:
		"weapon", "weapons":
			match index:
				1:
					return {"silver": 60, "bone_ash": 25, "cursed_iron": 2}
				2:
					return {"silver": 140, "bone_ash": 45, "cursed_iron": 6, "soul_cores": 1}
				_:
					return {}
		"armor", "armors":
			match index:
				1:
					return {"silver": 50, "bone_ash": 30, "cursed_iron": 1}
				2:
					return {"silver": 120, "bone_ash": 40, "cursed_iron": 5, "soul_cores": 1}
				3:
					return {"silver": 200, "bone_ash": 60, "cursed_iron": 8, "soul_cores": 3}
				_:
					return {}
		"spell", "spells":
			match index:
				1:
					return {"silver": 45, "bone_ash": 25, "soul_cores": 1}
				2:
					return {"silver": 110, "cursed_iron": 4, "soul_cores": 2}
				_:
					return {}
		"mod", "mods", "weapon_mod", "weapon_mods":
			match index:
				1:
					return {"silver": 40, "bone_ash": 20}
				2:
					return {"silver": 75, "bone_ash": 35, "cursed_iron": 2}
				3:
					return {"silver": 120, "cursed_iron": 4, "soul_cores": 2}
				_:
					return {}
		_:
			return {}


func craft_unlock_item(category: String, index: int, sub_index: int = 0) -> bool:
	var cat_norm: String = category.to_lower().strip_edges()
	match cat_norm:
		"weapon", "weapons":
			var w_idx: int = clampi(index, 0, 2)
			if is_weapon_unlocked(w_idx):
				return false
			var recipe: Dictionary = get_item_recipe("weapon", w_idx)
			if recipe.is_empty() or not spend_resources(recipe):
				return false
			unlocked_weapons[w_idx] = true
			equip_weapon(w_idx)
			_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, _sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_anvil_upgrade)
			if hud != null:
				hud.show_rpg_banner(
					"ARSENAL FORGED & EQUIPPED: %s" % get_active_weapon_display_name().to_upper(),
					Color(1.0, 0.84, 0.32, 1.0),
					3.2
				)
			_refresh_hud()
			loadout_changed.emit()
			return true

		"armor", "armors":
			var a_idx: int = clampi(index, 0, 3)
			if is_armor_unlocked(a_idx):
				return false
			var recipe_a: Dictionary = get_item_recipe("armor", a_idx)
			if recipe_a.is_empty() or not spend_resources(recipe_a):
				return false
			unlocked_armors[a_idx] = true
			equip_armor_tier(a_idx)
			_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, _sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_anvil_upgrade)
			if hud != null:
				hud.show_rpg_banner(
					"VESTMENTS FORGED & EQUIPPED: %s" % armor_tier_name.to_upper(),
					Color(1.0, 0.84, 0.32, 1.0),
					3.2
				)
			_refresh_hud()
			loadout_changed.emit()
			return true

		"spell", "spells":
			var s_idx: int = clampi(index, 0, 2)
			if is_spell_unlocked(s_idx):
				return false
			var recipe_s: Dictionary = get_item_recipe("spell", s_idx)
			if recipe_s.is_empty() or not spend_resources(recipe_s):
				return false
			unlocked_spells[s_idx] = true
			equip_lantern_spell(s_idx)
			_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, _sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_anvil_upgrade)
			if hud != null:
				var sp_catalog: Array[Dictionary] = get_lantern_spell_catalog()
				var sp_title: String = String(sp_catalog[s_idx].get("name", "Lantern Rite"))
				hud.show_rpg_banner(
					"LANTERN RITE CONSECRATED: %s" % sp_title.to_upper(),
					Color(1.0, 0.84, 0.32, 1.0),
					3.2
				)
			_refresh_hud()
			loadout_changed.emit()
			return true

		"mod", "mods", "weapon_mod", "weapon_mods":
			var w_idx_m: int = 0
			var m_idx: int = 0
			if cat_norm == "weapon_mod" and sub_index > 0 and index <= 2:
				w_idx_m = clampi(index, 0, 2)
				m_idx = clampi(sub_index, 0, 3)
			else:
				m_idx = clampi(index, 0, 3)
				w_idx_m = clampi(sub_index, 0, 2)
			if is_weapon_mod_unlocked(w_idx_m, m_idx):
				return false
			var recipe_m: Dictionary = get_item_recipe("mod", m_idx)
			if recipe_m.is_empty() or not spend_resources(recipe_m):
				return false
			var w_arr: Array = unlocked_weapon_mods[w_idx_m] as Array
			w_arr[m_idx] = true
			if not is_weapon_unlocked(w_idx_m):
				unlocked_weapons[w_idx_m] = true
			equip_weapon_mod(w_idx_m, m_idx)
			_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, _sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_anvil_upgrade)
			if hud != null:
				hud.show_rpg_banner(
					"ALCHEMICAL RITE FORGED: %s" % weapon_mod_name.to_upper(),
					Color(1.0, 0.84, 0.32, 1.0),
					3.2
				)
			_refresh_hud()
			loadout_changed.emit()
			return true
		_:
			return false


func grant_test_materials() -> void:
	add_resource("silver", 500)
	add_resource("bone_ash", 250)
	add_resource("cursed_iron", 50)
	add_resource("soul_cores", 20)
	_play_sfx(_sfx_ui_skill_chime if _sfx_ui_skill_chime != null else _sfx_loot_pickup, null)
	if hud != null:
		hud.show_rpg_banner(
			"SANCTUARY VAULT SUPPLIED: +500 SILVER, +250 BONE-ASH, +50 IRON, +20 SOUL-CORES",
			Color(1.0, 0.86, 0.34, 1.0),
			2.8
		)


func restore_full_vitality_and_armor() -> void:
	_recalculate_rpg_stats()
	current_health = max_health
	current_armor = max_armor
	if viewmodel_controller != null:
		viewmodel_controller.current_ammo = viewmodel_controller.max_ammo
		viewmodel_controller.ammo_changed.emit(viewmodel_controller.current_ammo, viewmodel_controller.max_ammo)
	_play_sfx(_sfx_sanctuary_heal, _sfx_ui_skill_chime)
	if hud != null:
		hud.show_rpg_banner(
			"BAPTISMAL FONT OF RITES — 100% VITALITY & ARMOR RESTORED",
			Color(0.45, 0.96, 0.78, 1.0),
			2.8
		)
	_refresh_hud()
	loadout_changed.emit()


static func get_relic_tier_for_biome(biome_id: int, is_boss_chest: bool = false) -> int:
	var eff_biome: int = clampi(biome_id + (2 if is_boss_chest else 0), 1, 8)
	if eff_biome <= 2:
		return 1
	elif eff_biome <= 4:
		return 2
	elif eff_biome <= 6:
		return 3
	return 4


static func get_relic_tier_title(tier: int) -> String:
	match clampi(tier, 1, 4):
		1:
			return "Tarnished Relic"
		2:
			return "Sanctified Relic"
		3:
			return "Blood-Forged Relic"
		_:
			return "Abyssal Sovereign Relic"


static func get_relic_tier_beam_color(tier: int) -> Color:
	match clampi(tier, 1, 4):
		1:
			return Color(1.0, 0.78, 0.35, 1.0)
		2:
			return Color(0.22, 0.96, 0.76, 1.0)
		3:
			return Color(0.92, 0.22, 0.78, 1.0)
		_:
			return Color(1.0, 0.85, 0.28, 1.0)


func grant_random_relic(biome_id: int, is_boss_chest: bool = false) -> Dictionary:
	var tier: int = get_relic_tier_for_biome(biome_id, is_boss_chest)
	var relic_id: int = clampi(((maxi(1, biome_id) - 1) % 8) + 1, 1, 8)
	var min_pct: float = 0.06
	var max_pct: float = 0.10
	var soul_regen: float = 0.0
	match tier:
		1:
			min_pct = 0.06
			max_pct = 0.10
		2:
			min_pct = 0.12
			max_pct = 0.18
		3:
			min_pct = 0.20
			max_pct = 0.28
		_:
			min_pct = 0.32
			max_pct = 0.45
			soul_regen = 0.25

	var bonus_pct: float = lerpf(min_pct, max_pct, 0.65)
	_relic_dmg_bonus += bonus_pct
	if tier >= 3:
		_relic_reload_bonus += bonus_pct * 0.5
		_relic_vit_bonus += roundf(bonus_pct * 60.0)
	if tier >= 4:
		_relic_soul_regen_bonus += soul_regen

	equipped_relic_tiers[relic_id] = maxi(int(equipped_relic_tiers.get(relic_id, 0)), tier)
	acquire_relic(relic_id)

	var tier_title: String = get_relic_tier_title(tier)
	var beam_col: Color = get_relic_tier_beam_color(tier)
	var r_entry: Dictionary = {
		"relic_id": relic_id,
		"tier": tier,
		"tier_title": tier_title,
		"bonus_pct": roundf(bonus_pct * 100.0),
		"soul_regen_pct": roundf(soul_regen * 100.0),
		"beam_color": beam_col
	}
	equipped_relic_data.append(r_entry)
	if hud != null:
		hud.show_rpg_banner(
			"%s UNEARTHED (+%.0f%% POTENCY)" % [tier_title.to_upper(), bonus_pct * 100.0],
			beam_col,
			3.8
		)
	_recalculate_rpg_stats()
	_refresh_hud()
	loadout_changed.emit()
	return r_entry


func acquire_relic(relic_id: int) -> void:
	var clamped_id: int = clampi(relic_id, 1, 8)
	var catalog: Dictionary[int, Dictionary] = LootDropPickup.get_relic_catalog()
	var r_name: String = "Occult Relic #%d" % clamped_id
	var r_desc: String = "Ancient Catacomb Blessing"
	var r_col: Color = Color(0.95, 0.65, 1.0, 1.0)

	if catalog.has(clamped_id):
		var info: Dictionary = catalog[clamped_id]
		r_name = str(info["name"])
		r_desc = str(info["desc"])
		r_col = info["color"] as Color

	if not active_relics.has(clamped_id):
		active_relics.append(clamped_id)
		active_relic_names.append(r_name)
	else:
		add_xp(25)

	_recalculate_rpg_stats()
	if hud != null:
		hud.show_rpg_banner(
			"RELIC ACQUIRED: %s — %s" % [r_name, r_desc],
			r_col,
			3.8
		)
		if viewmodel_controller != null:
			hud.update_spell_and_relics_display(
				viewmodel_controller.get_active_spell_name(),
				viewmodel_controller.ability_cooldown_remaining,
				active_relic_names,
				get_active_weapon_display_name()
			)
	_refresh_hud()
	loadout_changed.emit()


func grant_chest_rewards_batch(
	silver_amt: int,
	bone_ash_amt: int,
	iron_amt: int,
	cores_amt: int,
	xp_amt: int,
	relic_id_to_grant: int,
	biome_id: int = 1,
	is_boss_chest: bool = false,
	full_restore: bool = false
) -> void:
	if silver_amt > 0:
		crafting_resources["silver"] = get_resource_amount("silver") + silver_amt
		occult_essence += silver_amt
	if bone_ash_amt > 0:
		crafting_resources["bone_ash"] = get_resource_amount("bone_ash") + bone_ash_amt
	if iron_amt > 0:
		crafting_resources["cursed_iron"] = get_resource_amount("cursed_iron") + iron_amt
	if cores_amt > 0:
		crafting_resources["soul_cores"] = get_resource_amount("soul_cores") + cores_amt

	if xp_amt > 0:
		current_xp += xp_amt
		while current_xp >= xp_to_next_level:
			current_xp -= xp_to_next_level
			hunter_level += 1
			skill_points += 2
			unspent_attribute_points = skill_points
			xp_to_next_level = roundi(float(xp_to_next_level) * 1.35)

	var clamped_relic: int = clampi(relic_id_to_grant, 1, 8)
	var tier: int = get_relic_tier_for_biome(biome_id, is_boss_chest)
	var bonus_pct: float = 0.08 if tier == 1 else (0.15 if tier == 2 else (0.24 if tier == 3 else 0.38))
	var soul_regen: float = 0.25 if tier >= 4 else 0.0
	_relic_dmg_bonus += bonus_pct
	if tier >= 3:
		_relic_reload_bonus += bonus_pct * 0.5
		_relic_vit_bonus += roundf(bonus_pct * 60.0)
	if tier >= 4:
		_relic_soul_regen_bonus += soul_regen
	equipped_relic_tiers[clamped_relic] = maxi(int(equipped_relic_tiers.get(clamped_relic, 0)), tier)

	var catalog: Dictionary[int, Dictionary] = LootDropPickup.get_relic_catalog()
	var r_name: String = "Occult Relic #%d" % clamped_relic
	if catalog.has(clamped_relic):
		r_name = str((catalog[clamped_relic] as Dictionary)["name"])
	if not active_relics.has(clamped_relic):
		active_relics.append(clamped_relic)
		active_relic_names.append(r_name)

	var tier_title: String = get_relic_tier_title(tier)
	var beam_col: Color = get_relic_tier_beam_color(tier)
	equipped_relic_data.append({
		"relic_id": clamped_relic,
		"tier": tier,
		"tier_title": tier_title,
		"bonus_pct": roundf(bonus_pct * 100.0),
		"soul_regen_pct": roundf(soul_regen * 100.0),
		"beam_color": beam_col
	})

	_recalculate_rpg_stats()
	if full_restore:
		current_health = max_health
		current_armor = max_armor
		if viewmodel_controller != null:
			viewmodel_controller.current_ammo = viewmodel_controller.max_ammo
			viewmodel_controller.ammo_changed.emit(viewmodel_controller.current_ammo, viewmodel_controller.max_ammo)
	else:
		current_health = mini(max_health, current_health + 35)
		current_armor = mini(max_armor, current_armor + 25)

	if hud != null:
		hud.show_rpg_banner(
			"RELIQUARY CACHE UNSEALED — %s (+%d Silver)" % [r_name, silver_amt],
			beam_col,
			3.4
		)
	_refresh_hud()
	crafting_resources_changed.emit()
	loadout_changed.emit()


func apply_loot_pickup(
	category: String,
	xp_amt: int,
	essence_amt: int,
	hp_amt: int,
	armor_amt: int,
	relic_id: int,
	resource_key: String = "",
	resource_amt: int = 0,
	biome_tier: int = 1
) -> void:
	_play_sfx(_sfx_loot_pickup, null)

	var res_modified: bool = false
	if category == "silver" or category == "bone_ash" or category == "cursed_iron" or category == "soul_cores":
		var amt: int = resource_amt if resource_amt > 0 else maxi(1, essence_amt)
		crafting_resources[category] = get_resource_amount(category) + amt
		if category == "silver":
			occult_essence += amt
		res_modified = true
		if xp_amt > 0:
			add_xp(xp_amt)
			if res_modified:
				crafting_resources_changed.emit()
			return
	elif not resource_key.is_empty() and resource_amt > 0:
		crafting_resources[resource_key] = get_resource_amount(resource_key) + resource_amt
		if resource_key == "silver":
			occult_essence += resource_amt
		res_modified = true

	if category == "health":
		var scaled_hp_only: int = roundi(float(maxi(15, hp_amt)) * orb_recovery_mult)
		current_health = mini(max_health, current_health + scaled_hp_only)
		_refresh_hud()
		return
	elif category == "ammo":
		if viewmodel_controller != null:
			viewmodel_controller.current_ammo = viewmodel_controller.max_ammo
			viewmodel_controller.ammo_changed.emit(viewmodel_controller.current_ammo, viewmodel_controller.max_ammo)
		if armor_amt > 0:
			current_armor = mini(max_armor, current_armor + roundi(float(armor_amt) * orb_recovery_mult))
		_refresh_hud()
		return
	elif category == "xp_essence":
		occult_essence += essence_amt
		if not res_modified and essence_amt > 0:
			crafting_resources["silver"] = get_resource_amount("silver") + maxi(1, int(essence_amt / 2))
			res_modified = true
		if res_modified:
			crafting_resources_changed.emit()
		add_xp(xp_amt)
		return
	elif category == "elixir":
		var scaled_hp: int = roundi(float(hp_amt) * orb_recovery_mult)
		var scaled_arm: int = roundi(float(armor_amt) * orb_recovery_mult)
		current_health = mini(max_health, current_health + scaled_hp)
		current_armor = mini(max_armor, current_armor + scaled_arm)
		if viewmodel_controller != null:
			viewmodel_controller.current_ammo = viewmodel_controller.max_ammo
			viewmodel_controller.ammo_changed.emit(viewmodel_controller.current_ammo, viewmodel_controller.max_ammo)
		_refresh_hud()
		return
	elif category == "relic":
		if relic_id >= 1 and relic_id <= 8 and not active_relics.has(relic_id):
			acquire_relic(relic_id)
		else:
			grant_random_relic(maxi(1, biome_tier), false)
		return
	else:
		occult_essence += essence_amt
		if res_modified:
			crafting_resources_changed.emit()
		add_xp(xp_amt)
		return

	if res_modified:
		_refresh_hud()
		crafting_resources_changed.emit()
		loadout_changed.emit()


func on_enemy_killed() -> void:
	if hud != null:
		hud.trigger_hitmarker(true)
	if is_skill_unlocked("blood_2"):
		_blood_frenzy_timer = 4.0
		if viewmodel_controller != null:
			viewmodel_controller.current_ammo = mini(viewmodel_controller.max_ammo, viewmodel_controller.current_ammo + 1)
			viewmodel_controller.ammo_changed.emit(viewmodel_controller.current_ammo, viewmodel_controller.max_ammo)
	if is_skill_unlocked("blood_4"):
		_bloodlust_kill_stacks = mini(5, _bloodlust_kill_stacks + 1)
	if is_skill_unlocked("eld_3"):
		current_health = mini(max_health, current_health + 5)
		if viewmodel_controller != null:
			viewmodel_controller.ability_cooldown_remaining = maxf(0.0, viewmodel_controller.ability_cooldown_remaining - 0.75)
	if has_relic(8):
		current_health = mini(max_health, current_health + 15)
		_blood_frenzy_timer = 4.0

	_recalculate_rpg_stats()
	_refresh_hud()


func take_damage(raw_damage: float) -> void:
	apply_player_damage(raw_damage)


func take_player_damage(raw_damage: float) -> void:
	apply_player_damage(raw_damage)


func apply_player_damage(raw_damage: float) -> void:
	if raw_damage <= 0.0:
		return

	if player_controller == null:
		_resolve_dependencies()
	if player_controller != null and (player_controller.is_dashing_iframes or player_controller.dash_iframe_timer > 0.0):
		return

	var final_dmg: float = raw_damage * (1.0 - damage_reduction_ratio)
	if has_relic(4) and viewmodel_controller != null and viewmodel_controller.is_lantern_raised():
		final_dmg *= 0.80

	var total_dmg_int: int = maxi(1, roundi(final_dmg))
	var armor_share: int = 0
	if current_armor > 0:
		var max_armor_absorb: int = maxi(1, roundi(float(total_dmg_int) * 0.65))
		armor_share = mini(current_armor, max_armor_absorb)
		current_armor = maxi(0, current_armor - armor_share)

	var hp_damage: int = maxi(1, total_dmg_int - armor_share)
	current_health = maxi(0, current_health - hp_damage)

	if is_skill_unlocked("iron_4") and current_health > 0 and float(current_health) / float(maxi(1, max_health)) < 0.30:
		current_armor = mini(max_armor, current_armor + 40)

	_play_sfx(_sfx_player_hit, null)
	if player_controller != null:
		player_controller.add_camera_trauma(0.45, Vector3(deg_to_rad(4.2), 0.0, deg_to_rad(2.5)))
	if hud != null:
		hud.flash_portal_vignette(Color(0.95, 0.10, 0.16, 1.0))
	if viewmodel_controller != null:
		var flinch_immune: bool = is_skill_unlocked("iron_3") and viewmodel_controller.is_lantern_raised()
		if not flinch_immune:
			viewmodel_controller.add_recoil_impulse(Vector3(0.0, -0.015, 0.035), Vector3(deg_to_rad(7.5), 0.0, deg_to_rad(-3.0)))

	if current_health <= 0:
		_trigger_sanctuary_resurrection()
		return

	_refresh_hud()
	loadout_changed.emit()


func _trigger_sanctuary_resurrection() -> void:
	_play_sfx(_sfx_bell_resurrect, _sfx_sanctuary_heal)
	current_health = max_health
	current_armor = max_armor

	if viewmodel_controller != null:
		viewmodel_controller.current_ammo = viewmodel_controller.max_ammo
		viewmodel_controller.ammo_changed.emit(viewmodel_controller.current_ammo, viewmodel_controller.max_ammo)

	if player_controller != null:
		player_controller.global_position = Vector3(0.0, 3.6, -14.5)
		player_controller.velocity = Vector3.ZERO
		player_controller.rotation = Vector3(0.0, 0.0, 0.0)

	if hud != null:
		hud.flash_portal_vignette(Color(0.85, 0.05, 0.12, 1.0))
		hud.show_rpg_banner(
			"CONSUMED BY THE ABYSS — RESURRECTED AT SANCTUARY",
			Color(1.0, 0.24, 0.28, 1.0),
			4.2
		)

	_refresh_hud()
	loadout_changed.emit()


func cycle_weapon_mod(step: int = 1) -> void:
	var slot_idx: int = get_weapon_slot_index(active_weapon_id)
	var curr_mod: int = weapon_mod_indices[slot_idx]
	var dir_step: int = 1 if step >= 0 else -1
	for i: int in range(1, 5):
		var cand_mod: int = posmod(curr_mod + dir_step * i, 4)
		if is_weapon_mod_unlocked(slot_idx, cand_mod):
			if cand_mod != curr_mod:
				equip_weapon_mod(slot_idx, cand_mod)
			else:
				notify_locked_forge_required()
			return


func cycle_armor_tier(step: int = 1) -> void:
	var curr_arm: int = armor_tier_index
	var dir_step: int = 1 if step >= 0 else -1
	for i: int in range(1, 5):
		var cand_arm: int = posmod(curr_arm + dir_step * i, 4)
		if is_armor_unlocked(cand_arm):
			if cand_arm != curr_arm:
				equip_armor_tier(cand_arm)
			else:
				notify_locked_forge_required()
			return


func equip_armor(tier_idx: int) -> bool:
	return equip_armor_tier(tier_idx)


func equip_armor_slot(slot_name: String, set_idx: int) -> void:
	var s_key: String = slot_name.to_upper().strip_edges()
	if not ARMOR_SLOT_WEIGHTS.has(s_key):
		return
	var clamped_set: int = posmod(set_idx, 4)
	if not is_armor_piece_unlocked(s_key, clamped_set):
		notify_locked_forge_required()
		return
	equipped_armor_slots[s_key] = clamped_set
	if s_key == "HANDS":
		armor_tier_index = clamped_set
		equipped_armor_index = clamped_set
		_apply_first_person_gauntlet_visual(clamped_set)
	_recalculate_rpg_stats()
	_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, null)
	_refresh_hud()
	loadout_changed.emit()


func _apply_first_person_gauntlet_visual(gauntlet_set_idx: int) -> void:
	if viewmodel_controller == null:
		return
	var plate_col: Color = Color(0.24, 0.18, 0.14, 1.0)
	var plate_met: float = 0.45
	var plate_rough: float = 0.62
	var trim_col: Color = Color(0.52, 0.40, 0.22, 1.0)
	var leather_col: Color = Color(0.20, 0.12, 0.08, 1.0)
	match posmod(gauntlet_set_idx, 4):
		1:
			plate_col = Color(0.16, 0.22, 0.32, 1.0)
			plate_met = 0.88
			plate_rough = 0.34
			trim_col = Color(0.76, 0.78, 0.84, 1.0)
			leather_col = Color(0.12, 0.10, 0.14, 1.0)
		2:
			plate_col = Color(0.46, 0.36, 0.18, 1.0)
			plate_met = 0.82
			plate_rough = 0.52
			trim_col = Color(0.68, 0.54, 0.24, 1.0)
			leather_col = Color(0.22, 0.08, 0.10, 1.0)
		3:
			plate_col = Color(0.12, 0.08, 0.14, 1.0)
			plate_met = 0.88
			plate_rough = 0.30
			trim_col = Color(0.92, 0.18, 0.28, 1.0)
			leather_col = Color(0.32, 0.05, 0.08, 1.0)
	viewmodel_controller.equip_armor_gauntlet(gauntlet_set_idx, true)
	viewmodel_controller.apply_armor_tier(plate_col, plate_met, plate_rough, trim_col, leather_col)


func equip_armor_tier(tier_idx: int) -> bool:
	var target_idx: int = posmod(tier_idx, 4)
	if not is_armor_unlocked(target_idx):
		notify_locked_forge_required()
		return false

	armor_tier_index = target_idx
	equipped_armor_index = armor_tier_index
	for slot_k: String in ARMOR_SLOTS:
		unlock_armor_piece(slot_k, target_idx)
		equipped_armor_slots[slot_k] = target_idx

	_recalculate_rpg_stats()
	current_armor = max_armor
	_apply_first_person_gauntlet_visual(armor_tier_index)

	_play_sfx(_sfx_ui_armor_clank if _sfx_ui_armor_clank != null else _sfx_armor_equip, null)
	_refresh_hud()
	loadout_changed.emit()
	return true


func consecrate_sanctuary_upgrade() -> bool:
	if occult_essence < 50:
		return false

	occult_essence -= 50
	occult_blessing_level += 1
	_sanctuary_hp_bonus += 25
	lantern_radius_bonus += 2.5
	lantern_energy_bonus += 0.3
	_recalculate_rpg_stats()
	current_health = max_health
	current_armor = max_armor

	if viewmodel_controller != null:
		viewmodel_controller.apply_sanctuary_blessing(lantern_radius_bonus, lantern_energy_bonus)

	_play_sfx(_sfx_anvil_upgrade, _sfx_sanctuary_heal)
	_refresh_hud()
	loadout_changed.emit()
	return true


func _play_sfx(primary_stream: AudioStream, secondary_stream: AudioStream) -> void:
	if _sfx_player_primary != null and primary_stream != null and is_inside_tree():
		_sfx_player_primary.stream = primary_stream
		_sfx_player_primary.play()
	if _sfx_player_secondary != null and secondary_stream != null and is_inside_tree():
		_sfx_player_secondary.stream = secondary_stream
		_sfx_player_secondary.play()


func _refresh_hud() -> void:
	unspent_attribute_points = skill_points
	if hud != null:
		var attr_str: String = "BL:%d QS:%d IC:%d EF:%d" % [
			bloodlust_rank,
			quicksilver_rank,
			ironclad_rank,
			eldritch_rank
		]
		hud.update_status_bar(
			current_health,
			max_health,
			current_armor,
			armor_tier_name,
			occult_essence,
			weapon_mod_name,
			damage_per_shot,
			occult_blessing_level,
			hunter_level,
			current_xp,
			xp_to_next_level,
			max_armor,
			skill_points,
			attr_str,
			get_active_weapon_display_name()
		)
		if hud.has_method("update_crafting_resources"):
			hud.update_crafting_resources(
				get_resource_amount("silver"),
				get_resource_amount("bone_ash"),
				get_resource_amount("cursed_iron"),
				get_resource_amount("soul_cores")
			)
