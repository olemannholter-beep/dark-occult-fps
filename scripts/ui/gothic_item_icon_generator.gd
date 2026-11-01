class_name GothicItemIconGenerator
extends RefCounted

static var _icon_cache: Dictionary[String, Texture2D] = {}


static func get_or_create_thumbnail(slot_type: String, tier_idx: int = 0) -> Texture2D:
	var norm_slot: String = slot_type.to_upper().strip_edges()
	var clamped_tier: int = clampi(tier_idx, 0, 7)
	var cache_key: String = "%s_%d" % [norm_slot, clamped_tier]
	if _icon_cache.has(cache_key):
		return _icon_cache[cache_key]

	var is_armor_slot: bool = norm_slot in ["HEAD", "CHEST", "HANDS", "LEGS", "FEET"]
	if not (is_armor_slot and clamped_tier in [1, 2, 3]):
		var file_candidates: Array[String] = [
			"res://assets/ui/icons/%s_%d.png" % [norm_slot.to_lower(), clamped_tier],
			"res://assets/ui/icons/%s.png" % norm_slot.to_lower()
		]
		for path: String in file_candidates:
			if ResourceLoader.exists(path):
				var loaded_tex: Texture2D = load(path) as Texture2D
				if loaded_tex != null:
					_icon_cache[cache_key] = loaded_tex
					return loaded_tex


	var img: Image = Image.create(64, 64, false, Image.FORMAT_RGBA8)
	_draw_vignette_background(img, clamped_tier % 4)
	match norm_slot:
		"HEAD":
			_draw_head_icon(img, clamped_tier % 4)
		"CHEST":
			_draw_chest_icon(img, clamped_tier % 4)
		"HANDS":
			_draw_hands_icon(img, clamped_tier % 4)
		"LEGS":
			_draw_legs_icon(img, clamped_tier % 4)
		"FEET":
			_draw_feet_icon(img, clamped_tier % 4)
		"FIREARM", "WEAPON":
			_draw_firearm_icon(img, clamped_tier % 3)
		"SPELL", "LANTERN":
			_draw_spell_icon(img, clamped_tier % 3)
		"RELIC":
			_draw_relic_icon(img, clamped_tier)
		"MATERIAL":
			_draw_material_icon(img, clamped_tier % 4)
		_:
			_draw_relic_icon(img, clamped_tier)

	var tex: ImageTexture = ImageTexture.create_from_image(img)
	_icon_cache[cache_key] = tex
	return tex


static func _draw_vignette_background(img: Image, set_tier: int) -> void:
	var bg_colors: Array[Color] = [
		Color.html("#2b2118"), # Set 0: Weathered Umber
		Color.html("#1e242b"), # Set 1: Steel Slate
		Color.html("#231a2e"), # Set 2: Deep Violet
		Color.html("#2e1b14")  # Set 3: Scorched Ember
	]
	var rim_colors: Array[Color] = [
		Color.html("#6e5539"),
		Color.html("#56697a"),
		Color.html("#684c85"),
		Color.html("#8a4829")
	]
	var center_col: Color = bg_colors[posmod(set_tier, 4)]
	var rim_col: Color = rim_colors[posmod(set_tier, 4)]
	var edge_dark: Color = Color(0.04, 0.04, 0.05, 1.0)
	for y: int in range(64):
		for x: int in range(64):
			var dx: float = (float(x) - 31.5) / 31.5
			var dy: float = (float(y) - 31.5) / 31.5
			var dist: float = clampf(sqrt(dx * dx + dy * dy), 0.0, 1.25)
			var c: Color = center_col.lerp(edge_dark, clampf(dist * 0.82, 0.0, 1.0))
			if x == 1 or x == 62 or y == 1 or y == 62:
				c = rim_col.darkened(0.35)
			elif (x <= 4 or x >= 59) and (y <= 4 or y >= 59):
				c = rim_col
			img.set_pixel(x, y, c)


static func _fill_rect(img: Image, x0: int, y0: int, w: int, h: int, col: Color) -> void:
	for y: int in range(maxi(2, y0), mini(62, y0 + h)):
		for x: int in range(maxi(2, x0), mini(62, x0 + w)):
			img.set_pixel(x, y, col)


static func _fill_circle(img: Image, cx: float, cy: float, rad: float, col: Color) -> void:
	var r2: float = rad * rad
	var min_x: int = maxi(2, int(floorf(cx - rad)))
	var max_x: int = mini(61, int(ceilf(cx + rad)))
	var min_y: int = maxi(2, int(floorf(cy - rad)))
	var max_y: int = mini(61, int(ceilf(cy + rad)))
	for y: int in range(min_y, max_y + 1):
		for x: int in range(min_x, max_x + 1):
			var dx: float = float(x) - cx
			var dy: float = float(y) - cy
			if dx * dx + dy * dy <= r2:
				img.set_pixel(x, y, col)


static func _draw_line(img: Image, x0: int, y0: int, x1: int, y1: int, thick: int, col: Color) -> void:
	var steps: int = maxi(absi(x1 - x0), absi(y1 - y0))
	if steps == 0:
		_fill_rect(img, x0, y0, thick, thick, col)
		return
	for i: int in range(steps + 1):
		var t: float = float(i) / float(steps)
		var px: int = roundi(lerpf(float(x0), float(x1), t))
		var py: int = roundi(lerpf(float(y0), float(y1), t))
		_fill_rect(img, px - thick / 2, py - thick / 2, thick, thick, col)


static func _draw_head_icon(img: Image, tier: int) -> void:
	match tier:
		0: # Hooded death-mask & tricorn
			var leather_dk: Color = Color.html("#1b1410")
			var leather_mid: Color = Color.html("#4a3728")
			var leather_hi: Color = Color.html("#785a42")
			var brass: Color = Color.html("#e0b252")
			# Tricorn wide brim & crown
			_draw_line(img, 8, 25, 56, 25, 4, leather_dk)
			_draw_line(img, 10, 24, 32, 11, 5, leather_mid)
			_draw_line(img, 54, 24, 32, 11, 5, leather_mid)
			_fill_rect(img, 20, 14, 24, 11, leather_mid)
			_draw_line(img, 12, 23, 32, 12, 2, leather_hi)
			# Shadowed hood & death-mask
			_fill_circle(img, 32.0, 38.0, 14.0, leather_dk)
			_fill_rect(img, 23, 28, 18, 20, Color.html("#362b24"))
			_fill_rect(img, 25, 30, 14, 15, Color.html("#6e5d4f"))
			# Glowing ocular lenses & respirator rivets
			_fill_rect(img, 25, 33, 5, 3, brass)
			_fill_rect(img, 34, 33, 5, 3, brass)
			_fill_rect(img, 30, 39, 4, 7, leather_dk)
		1: # Winged Ember-Visor Barbute (Set 1)
			var steel_dk: Color = Color.html("#22252a")
			var steel_mid: Color = Color.html("#383d46")
			var steel_hi: Color = Color.html("#727c8c")
			var bronze: Color = Color.html("#8c734b")
			var ember: Color = Color.html("#ff5511")
			# Swept-back feathered dark-iron temple wings at 35° + bronze base mounts
			_draw_line(img, 18, 32, 6, 12, 4, steel_mid)
			_draw_line(img, 46, 32, 58, 12, 4, steel_mid)
			_draw_line(img, 18, 36, 9, 20, 3, steel_hi)
			_draw_line(img, 46, 36, 55, 20, 3, steel_hi)
			_fill_rect(img, 15, 28, 5, 6, bronze)
			_fill_rect(img, 44, 28, 5, 6, bronze)
			# Rounded fluted barbute dome & cheek plates
			_fill_circle(img, 32.0, 29.0, 14.0, steel_dk)
			_fill_circle(img, 30.0, 25.0, 10.0, steel_mid)
			_fill_rect(img, 19, 26, 26, 24, steel_dk)
			# Raised central cranial ridge + bronze trim
			_fill_rect(img, 30, 12, 4, 38, steel_hi)
			_fill_rect(img, 19, 48, 26, 3, bronze)
			# Recessed vertical visor grill slits (4 narrow bars over glowing #ff5511 ember interior)
			_fill_rect(img, 22, 30, 20, 10, ember)
			for gx: int in [24, 28, 35, 39]:
				_fill_rect(img, gx, 30, 2, 10, steel_dk)
		2: # Tall Ocular Mitre-Helm (Set 2)
			var vio_dk: Color = Color.html("#120f18")
			var vio_mid: Color = Color.html("#262230")
			var vio_trim: Color = Color.html("#5e5473")
			var glow: Color = Color.html("#8822cc")
			# Pointed bishop/inquisitor mitre spire + silver-violet trim borders
			_draw_line(img, 19, 46, 32, 8, 9, vio_mid)
			_draw_line(img, 45, 46, 32, 8, 9, vio_mid)
			_draw_line(img, 18, 46, 32, 7, 2, vio_trim)
			_draw_line(img, 46, 46, 32, 7, 2, vio_trim)
			_fill_rect(img, 20, 28, 24, 24, vio_mid)
			_fill_rect(img, 31, 10, 2, 40, vio_trim)
			# Etched all-seeing ocular sigil on the brow
			_fill_circle(img, 32.0, 22.0, 5.0, vio_trim)
			_fill_circle(img, 32.0, 22.0, 3.0, glow)
			# Recessed T-visor faceguard
			_fill_rect(img, 22, 32, 20, 4, vio_dk)
			_fill_rect(img, 30, 34, 4, 16, vio_dk)
			_fill_circle(img, 26.0, 34.0, 1.8, glow)
			_fill_circle(img, 38.0, 34.0, 1.8, glow)
		_: # Crowned Ossuary Skull & Spiked Iron Halo (Set 3)
			var iron: Color = Color.html("#242220")
			var iron_hi: Color = Color.html("#4a4542")
			var bone: Color = Color.html("#b8a68e")
			var bone_sh: Color = Color.html("#9c8c74")
			var void_dk: Color = Color.html("#110e0c")
			var ember: Color = Color.html("#ff6611")
			# Spiked iron halo ring mounted behind the cranium
			_fill_circle(img, 32.0, 30.0, 22.0, iron_hi)
			_fill_circle(img, 32.0, 30.0, 18.5, Color.html("#1c120e"))
			for h_ang: int in range(0, 360, 30):
				var rad_a: float = deg_to_rad(float(h_ang))
				_draw_line(img, roundi(32.0 + cos(rad_a) * 20.0), roundi(30.0 + sin(rad_a) * 20.0), roundi(32.0 + cos(rad_a) * 26.0), roundi(30.0 + sin(rad_a) * 26.0), 2, iron_hi)
			# Sculpted bleached bone skull visage + dark recessed eye sockets & nasal cavity
			_fill_circle(img, 32.0, 35.0, 12.5, bone)
			_fill_rect(img, 24, 42, 16, 11, bone_sh)
			_fill_circle(img, 27.0, 35.0, 3.8, void_dk)
			_fill_circle(img, 37.0, 35.0, 3.8, void_dk)
			_fill_circle(img, 27.0, 35.0, 1.5, ember)
			_fill_circle(img, 37.0, 35.0, 1.5, ember)
			_fill_rect(img, 31, 38, 2, 4, void_dk)
			# Jagged dark-iron crown encircling the brow
			for sx: int in [19, 25, 32, 39, 45]:
				_draw_line(img, sx, 25, sx, 14, 3, iron)
			_fill_rect(img, 18, 23, 28, 4, iron)


static func _draw_chest_icon(img: Image, tier: int) -> void:
	match tier:
		0: # Shoulder-candle mantle & grimoire strap (Set 0 untouched)
			var coat: Color = Color.html("#3d2c1e")
			var cape: Color = Color.html("#5e442f")
			var brass: Color = Color.html("#ebb952")
			_fill_rect(img, 14, 18, 36, 14, cape)
			_fill_rect(img, 18, 26, 28, 28, coat)
			# Diagonal bandolier strap + buckles
			_draw_line(img, 18, 20, 44, 50, 5, Color.html("#7a5638"))
			_fill_rect(img, 28, 32, 6, 6, brass)
			# Shoulder wax candle + flame
			_fill_rect(img, 43, 11, 4, 8, Color.html("#e8dec8"))
			_fill_circle(img, 45.0, 8.0, 3.0, Color.html("#ffaa22"))
		1: # Fluted Cross Cuirass & 4-Lame Shingled Pauldrons (Set 1)
			var steel: Color = Color.html("#22252a")
			var flute_hi: Color = Color.html("#383d46")
			var bronze: Color = Color.html("#8c734b")
			# 4-tier shingled pauldrons with bronze rims
			for l_i: int in range(4):
				var py: int = 18 + l_i * 5
				_fill_rect(img, 8, py, 11, 4, steel)
				_fill_rect(img, 45, py, 11, 4, steel)
				_fill_rect(img, 8, py + 3, 11, 1, bronze)
				_fill_rect(img, 45, py + 3, 11, 1, bronze)
			# V-tapered fluted breastplate + high flanged gorget collar
			_fill_rect(img, 18, 16, 28, 36, steel)
			_fill_rect(img, 22, 12, 20, 5, steel)
			_fill_rect(img, 22, 12, 20, 2, bronze)
			for fx: int in range(20, 44, 4):
				_fill_rect(img, fx, 18, 2, 32, flute_hi)
			# Bold raised forged-iron Synod cross on sternum
			_fill_rect(img, 30, 19, 4, 28, bronze)
			_fill_rect(img, 22, 26, 20, 4, bronze)
		2: # Heavy Layered Carapace Cuirass with Nocturnite Veins (Set 2)
			var cara: Color = Color.html("#221f2b")
			var cara_hi: Color = Color.html("#5e5473")
			var vein: Color = Color.html("#8822cc")
			_fill_circle(img, 14.0, 24.0, 9.0, cara)
			_fill_circle(img, 50.0, 24.0, 9.0, cara)
			for ly: int in range(16, 50, 7):
				_fill_rect(img, 16, ly, 32, 6, cara)
				_draw_line(img, 18, ly + 1, 32, ly + 5, 2, cara_hi)
				_draw_line(img, 46, ly + 1, 32, ly + 5, 2, cara_hi)
				_draw_line(img, 20, ly + 3, 32, ly + 6, 1, vein)
				_draw_line(img, 44, ly + 3, 32, ly + 6, 1, vein)
			_fill_rect(img, 31, 18, 2, 30, vein)
		_: # Skeletal Iron Ribcage, Glowing Cinder Runes, Shoulder Candles & Hanging Censers (Set 3)
			var core: Color = Color.html("#110e0c")
			var iron_rib: Color = Color.html("#2a2624")
			var bone_st: Color = Color.html("#9c8c74")
			var cinder: Color = Color.html("#ff6611")
			var wax: Color = Color.html("#d8c39e")
			# Charred core + glowing vertical cinder runes down sternum
			_fill_rect(img, 18, 16, 28, 34, core)
			_fill_rect(img, 29, 18, 6, 30, cinder)
			# Anatomical ribs & bone sternum
			for ry: int in range(20, 48, 6):
				_fill_rect(img, 16, ry, 32, 3, iron_rib)
			_fill_rect(img, 27, 17, 2, 32, bone_st)
			_fill_rect(img, 35, 17, 2, 32, bone_st)
			# Shoulder candle clusters + hanginghip reliquary censers
			for sx: int in [12, 16, 48, 52]:
				_fill_rect(img, sx, 10, 2, 6, wax)
				_fill_circle(img, float(sx) + 1.0, 8.0, 2.0, Color.html("#ff8811"))
			_draw_line(img, 11, 24, 11, 46, 2, iron_rib)
			_draw_line(img, 53, 24, 53, 46, 2, iron_rib)
			_fill_circle(img, 11.0, 50.0, 4.0, Color.html("#ff7722"))
			_fill_circle(img, 53.0, 50.0, 4.0, Color.html("#ff7722"))



static func _draw_hands_icon(img: Image, tier: int) -> void:
	var base_c: Color = [Color.html("#59412e"), Color.html("#22252a"), Color.html("#221f2b"), Color.html("#242220")][tier]
	var hi_c: Color = [Color.html("#7d5b40"), Color.html("#383d46"), Color.html("#5e5473"), Color.html("#b8a68e")][tier]
	var trim_c: Color = [Color.html("#d4a446"), Color.html("#8c734b"), Color.html("#8822cc"), Color.html("#ff6611")][tier]
	# Left & right angled gauntlets
	_draw_line(img, 14, 46, 24, 18, 9, base_c)
	_draw_line(img, 36, 46, 48, 18, 9, base_c)
	_draw_line(img, 14, 44, 23, 19, 3, hi_c)
	_draw_line(img, 36, 44, 47, 19, 3, hi_c)
	# Wrist chain / knuckle trim / spikes (Set 2) / skeletal finger bones (Set 3)
	_draw_line(img, 12, 34, 26, 36, 3, trim_c)
	_draw_line(img, 34, 34, 50, 36, 3, trim_c)
	if tier == 2:
		for sy: int in [24, 32, 40]:
			_draw_line(img, 12, sy, 6, sy - 3, 2, hi_c)
			_draw_line(img, 46, sy, 52, sy - 3, 2, hi_c)


static func _draw_legs_icon(img: Image, tier: int) -> void:
	var base_c: Color = [Color.html("#4a3626"), Color.html("#22252a"), Color.html("#221f2b"), Color.html("#242220")][tier]
	var hi_c: Color = [Color.html("#694d36"), Color.html("#383d46"), Color.html("#5e5473"), Color.html("#b8a68e")][tier]
	var trim_c: Color = [Color.html("#cfa044"), Color.html("#8c734b"), Color.html("#8822cc"), Color.html("#ff6611")][tier]
	# Belt waist + twin greaves
	_fill_rect(img, 16, 12, 32, 6, trim_c)
	_fill_rect(img, 17, 18, 12, 34, base_c)
	_fill_rect(img, 35, 18, 12, 34, base_c)
	_fill_rect(img, 19, 20, 4, 30, hi_c)
	_fill_rect(img, 37, 20, 4, 30, hi_c)
	if tier == 1:
		# Chainmail V-hang between upper thighs
		_fill_rect(img, 29, 18, 6, 12, Color.html("#181a1d"))
	elif tier == 3:
		# Glowing cinder-rune front tabard strip
		_fill_rect(img, 30, 18, 4, 28, trim_c)
	# Knee poleyns / knee skulls
	_fill_circle(img, 23.0, 33.0, 5.0, hi_c if tier == 3 else trim_c)
	_fill_circle(img, 41.0, 33.0, 5.0, hi_c if tier == 3 else trim_c)


static func _draw_feet_icon(img: Image, tier: int) -> void:
	var base_c: Color = [Color.html("#422f20"), Color.html("#22252a"), Color.html("#221f2b"), Color.html("#242220")][tier]
	var hi_c: Color = [Color.html("#5e432d"), Color.html("#383d46"), Color.html("#5e5473"), Color.html("#4a4542")][tier]
	var trim_c: Color = [Color.html("#d6a648"), Color.html("#8c734b"), Color.html("#8822cc"), Color.html("#ff6611")][tier]
	# Twin boots / sabatons profile
	_fill_rect(img, 14, 16, 13, 28, base_c)
	_fill_rect(img, 14, 38, 20, 11, base_c)
	_fill_rect(img, 35, 16, 13, 28, base_c)
	_fill_rect(img, 35, 38, 20, 11, base_c)
	_fill_rect(img, 16, 18, 4, 24, hi_c)
	_fill_rect(img, 37, 18, 4, 24, hi_c)
	# Buckles & soles / bronze toe trim / cinder vents
	_fill_rect(img, 13, 47, 22, 3, trim_c)
	_fill_rect(img, 34, 47, 22, 3, trim_c)



static func _draw_firearm_icon(img: Image, weap_idx: int) -> void:
	var steel: Color = Color.html("#8b9bb0")
	var steel_hi: Color = Color.html("#cad8eb")
	var grip: Color = Color.html("#593922")
	var brass: Color = Color.html("#ebbf5b")
	if weap_idx == 1: # Hellfire Coach Gun
		_draw_line(img, 10, 46, 24, 32, 7, grip)
		_draw_line(img, 22, 32, 54, 18, 7, steel)
		_draw_line(img, 22, 29, 54, 15, 3, Color.html("#ff6e26"))
	elif weap_idx == 2: # Pneumatic Stake-Driver
		_fill_rect(img, 12, 24, 32, 14, brass)
		_draw_line(img, 42, 31, 56, 31, 5, steel_hi)
		_draw_line(img, 18, 38, 14, 50, 6, grip)
	else: # Occult Revolver
		_draw_line(img, 12, 47, 22, 31, 8, grip)
		_fill_rect(img, 21, 24, 14, 11, brass)
		_fill_rect(img, 20, 21, 34, 6, steel)
		_fill_rect(img, 22, 22, 30, 2, steel_hi)


static func _draw_spell_icon(img: Image, spell_idx: int) -> void:
	var brass: Color = Color.html("#d4a446")
	var flame_outer: Color = [Color.html("#ff6a1a"), Color.html("#9b4dff"), Color.html("#38d6ff")][spell_idx]
	var flame_core: Color = Color.html("#fff3b8")
	# Lantern cage & top ring
	_fill_circle(img, 32.0, 12.0, 4.0, brass)
	_fill_rect(img, 20, 16, 24, 4, brass)
	_fill_rect(img, 18, 48, 28, 5, brass)
	_draw_line(img, 21, 18, 20, 48, 2, brass)
	_draw_line(img, 43, 18, 44, 48, 2, brass)
	# Burning consecration flame
	_fill_circle(img, 32.0, 34.0, 10.0, flame_outer)
	_fill_circle(img, 32.0, 31.0, 6.0, flame_core)


static func _draw_relic_icon(img: Image, relic_idx: int) -> void:
	var gold: Color = Color.html("#e3b44c")
	var bone: Color = Color.html("#ded2ba")
	var gem: Color = Color.html("#3ae68a") if (relic_idx % 2 == 0) else Color.html("#ff4757")
	_fill_circle(img, 32.0, 34.0, 17.0, gold)
	_fill_circle(img, 32.0, 36.0, 11.0, Color.html("#1a151c"))
	_fill_circle(img, 32.0, 22.0, 9.0, bone)
	_fill_rect(img, 28, 28, 8, 6, bone)
	_fill_circle(img, 29.0, 22.0, 2.2, gem)
	_fill_circle(img, 35.0, 22.0, 2.2, gem)


static func _draw_material_icon(img: Image, mat_idx: int) -> void:
	var cols: Array[Color] = [
		Color.html("#cfd9e6"), # Silver
		Color.html("#d9c8a9"), # Bone-Ash
		Color.html("#6e7b8b"), # Cursed Iron
		Color.html("#ff8c2b")  # Soul-Core
	]
	var c: Color = cols[posmod(mat_idx, 4)]
	_fill_circle(img, 32.0, 32.0, 15.0, c.darkened(0.35))
	_fill_circle(img, 30.0, 29.0, 10.0, c)
	_fill_circle(img, 28.0, 26.0, 4.0, Color.WHITE)
