extends GdUnitTestSuite


func test_main_scene_loads() -> void:
	var packed: PackedScene = load("res://src/game/main.tscn") as PackedScene
	assert_object(packed).is_not_null()


func test_smoke_is_inactive_without_flag() -> void:
	var parent: Node = auto_free(Node.new())
	assert_bool(Smoke.attach_if_requested(parent)).is_false()
