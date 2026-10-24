extends Control
## Temporary entry scene; replace with the approved game home screen.


func _ready() -> void:
	var title := Label.new()
	title.text = "{{GAME_NAME}}"
	title.add_theme_font_size_override("font_size", 72)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(title)
	Smoke.attach_if_requested(self)
