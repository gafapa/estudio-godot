extends SceneTree
## Render a scene in an exact-size SubViewport with optional fixture metadata.

var _size: Vector2i = Vector2i(1920, 1080)
var _frames: int = 10
var _out: String = ""
var _frame: int = 0
var _done: bool = false
var _view: SubViewport


func _initialize() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() < 4:
		_fail("Usage: <scene> <WxH> <frames> <out.png> [fixture]")
		return
	var scene_path: String = args[0]
	var parts: PackedStringArray = args[1].split("x")
	if parts.size() != 2:
		_fail("Invalid resolution: %s" % args[1])
		return
	_size = Vector2i(int(parts[0]), int(parts[1]))
	if _size.x < 1 or _size.y < 1 or _size.x > 16384 or _size.y > 16384:
		_fail("Resolution outside supported limits")
		return
	_frames = int(args[2])
	if _frames < 1 or _frames > 10000:
		_fail("Frame count outside supported limits")
		return
	_out = args[3]
	if args.size() > 4 and args[4] != "":
		Engine.set_meta("fixture_path", args[4])
	var packed: Resource = ResourceLoader.load(scene_path)
	if not packed is PackedScene:
		_fail("Could not load scene: %s" % scene_path)
		return
	var inst: Node = (packed as PackedScene).instantiate()
	if inst == null:
		_fail("Could not instantiate: %s" % scene_path)
		return
	_view = SubViewport.new()
	_view.size = _size
	_view.own_world_3d = true
	_view.transparent_bg = false
	_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_apply_stretch(_view)
	root.add_child(_view)
	_view.add_child(inst)


func _apply_stretch(view: SubViewport) -> void:
	var mode: String = str(ProjectSettings.get_setting("display/window/stretch/mode", "disabled"))
	if mode != "canvas_items":
		return
	var base := Vector2(
		float(ProjectSettings.get_setting("display/window/size/viewport_width", _size.x)),
		float(ProjectSettings.get_setting("display/window/size/viewport_height", _size.y))
	)
	var scale: float = minf(float(_size.x) / base.x, float(_size.y) / base.y)
	if scale <= 0.0:
		return
	view.size_2d_override = Vector2i(roundi(_size.x / scale), roundi(_size.y / scale))
	view.size_2d_override_stretch = true


func _process(_delta: float) -> bool:
	if _done:
		return false
	_frame += 1
	if _frame < _frames:
		return false
	_done = true
	var img: Image = _view.get_texture().get_image()
	if img == null or img.is_empty():
		_fail("Empty viewport image")
		return true
	DirAccess.make_dir_recursive_absolute(_out.get_base_dir())
	var err: Error = img.save_png(_out)
	if err != OK:
		_fail("Could not save %s (error %d)" % [_out, err])
		return true
	print("SCREENSHOT_OK %s %dx%d" % [_out, img.get_width(), img.get_height()])
	quit(0)
	return true


func _fail(msg: String) -> void:
	_done = true
	printerr("SCREENSHOT_FAIL: " + msg)
	quit(1)
