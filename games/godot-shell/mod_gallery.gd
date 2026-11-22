extends CanvasLayer
# Mod: every scene artwork of the game, unlocked. A page of 12 previews at a
# time (only that page is loaded); tap one to see it full screen, then tap
# the right or left half for the next or previous one.

const COLUMNS = 4
const PER_PAGE = 12

var images = []
var page = 0
var current = -1

var grid: GridContainer
var page_label: Label
var viewer: Control
var viewer_image: TextureRect
var viewer_label: Label

func _ready():
	layer = 100

	var background = ColorRect.new()
	background.color = Color(0.05, 0.05, 0.07, 1)
	background.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(background)

	var bar = HBoxContainer.new()
	bar.set_anchors_preset(Control.PRESET_TOP_WIDE)
	bar.offset_left = 16
	bar.offset_right = -16
	bar.offset_top = 10
	bar.offset_bottom = 64
	bar.add_theme_constant_override("separation", 16)
	background.add_child(bar)
	bar.add_child(_make_button("Close", queue_free))
	bar.add_child(_make_button("<", _turn_page.bind(-1)))
	page_label = Label.new()
	page_label.custom_minimum_size = Vector2(220, 0)
	page_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	page_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	page_label.add_theme_font_size_override("font_size", 26)
	bar.add_child(page_label)
	bar.add_child(_make_button(">", _turn_page.bind(1)))

	grid = GridContainer.new()
	grid.columns = COLUMNS
	grid.set_anchors_preset(Control.PRESET_FULL_RECT)
	grid.offset_left = 16
	grid.offset_right = -16
	grid.offset_top = 76
	grid.offset_bottom = -12
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	background.add_child(grid)

	viewer = ColorRect.new()
	viewer.color = Color(0, 0, 0, 1)
	viewer.set_anchors_preset(Control.PRESET_FULL_RECT)
	viewer.visible = false
	viewer.gui_input.connect(_on_viewer_input)
	add_child(viewer)
	viewer_image = TextureRect.new()
	viewer_image.set_anchors_preset(Control.PRESET_FULL_RECT)
	viewer_image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	viewer_image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	viewer_image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	viewer.add_child(viewer_image)
	viewer_label = Label.new()
	viewer_label.position = Vector2(16, 8)
	viewer_label.add_theme_font_size_override("font_size", 22)
	viewer_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	viewer.add_child(viewer_label)
	var close = _make_button("Back", _close_viewer)
	close.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	close.offset_left = -150
	close.offset_right = -16
	close.offset_top = 10
	close.offset_bottom = 64
	viewer.add_child(close)

	_show_page()

func _make_button(text, callback):
	var button = Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(120, 54)
	button.add_theme_font_size_override("font_size", 24)
	button.pressed.connect(callback)
	return button

func _page_count():
	return max(1, int(ceil(images.size() / float(PER_PAGE))))

func _turn_page(step):
	page = posmod(page + step, _page_count())
	_show_page()

func _show_page():
	for child in grid.get_children():
		grid.remove_child(child)
		child.queue_free()
	page_label.text = "%d / %d" % [page + 1, _page_count()]
	for i in range(page * PER_PAGE, min(images.size(), (page + 1) * PER_PAGE)):
		var preview = TextureButton.new()
		preview.texture_normal = load(images[i])
		preview.ignore_texture_size = true
		preview.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		preview.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		preview.size_flags_vertical = Control.SIZE_EXPAND_FILL
		preview.pressed.connect(_open_viewer.bind(i))
		grid.add_child(preview)

func _open_viewer(index):
	current = posmod(index, images.size())
	viewer_image.texture = load(images[current])
	viewer_label.text = "%d / %d   %s" % [current + 1, images.size(), images[current].get_file().get_basename()]
	viewer.visible = true

func _close_viewer():
	viewer.visible = false
	viewer_image.texture = null
	var wanted = int(current / PER_PAGE)
	if wanted != page:
		page = wanted
		_show_page()

func _on_viewer_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var step = 1 if event.position.x > viewer.size.x / 2 else -1
		_open_viewer(current + step)
		get_viewport().set_input_as_handled()
