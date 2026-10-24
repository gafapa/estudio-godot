class_name Smoke
extends Node
## Desktop smoke exits after a few frames; Android debug keeps running.

const FRAMES: int = 30

var _frame: int = 0
var _quit_when_done: bool = false


static func attach_if_requested(parent: Node) -> bool:
	var wants_quit: bool = (
		"--smoke" in OS.get_cmdline_user_args() or "--smoke" in OS.get_cmdline_args()
	)
	var android_debug: bool = OS.has_feature("android") and OS.is_debug_build()
	if not wants_quit and not android_debug:
		return false
	var smoke := Smoke.new()
	smoke._quit_when_done = wants_quit
	parent.add_child(smoke)
	return true


func _process(_delta: float) -> void:
	_frame += 1
	if _frame < FRAMES:
		return
	set_process(false)
	print("SMOKE_OK")
	if _quit_when_done:
		get_tree().quit(0)
