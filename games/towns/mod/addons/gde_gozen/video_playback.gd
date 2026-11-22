class_name VideoPlayback
extends Control
## Stand-in for GDE GoZen's VideoPlayback on iOS, where GoZen has no library:
## the same signals and the calls Town's Charm makes, played by Godot's own
## VideoStreamPlayer. The game's .mp4 files are re-encoded as Ogg Theora in
## the build (keeping their names), which VideoStreamTheora reads by content.

signal frame_changed(frame_nr: int)
signal next_frame_called(frame_nr: int)
signal video_loaded
signal video_ended
signal playback_started
signal playback_paused
signal playback_ready

@export_file var path: String = "": set = set_video_path
@export var enable_audio: bool = true: set = _set_enable_audio
@export var audio_speed_to_sync: bool = false
@export var enable_auto_play: bool = false
@export var playback_speed: float = 1.0
@export var pitch_adjust: bool = true
@export var loop: bool = false
@export var color_profile: int = 0
@export var debug: bool = false

var is_playing: bool = false
var current_frame: int = 0

var _player: VideoStreamPlayer = VideoStreamPlayer.new()
var _open: bool = false


func _enter_tree() -> void:
	if _player.get_parent() == null:
		_player.set_anchors_preset(Control.PRESET_FULL_RECT)
		_player.expand = true
		_player.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_player.finished.connect(_on_finished)
		add_child(_player, false, Node.INTERNAL_MODE_FRONT)
	_set_enable_audio(enable_audio)


func _ready() -> void:
	playback_ready.emit()
	if path != "" and not _open:
		set_video_path(path)


func set_video_path(new_path: String) -> void:
	path = new_path
	if not is_inside_tree():
		return
	close()
	if new_path == "":
		return
	var stream := VideoStreamTheora.new()
	stream.file = new_path
	_player.stream = stream
	_open = true
	current_frame = 0
	video_loaded.emit.call_deferred()
	if enable_auto_play:
		play.call_deferred()


func play() -> void:
	if not _open:
		return
	if _player.paused:
		_player.paused = false
	elif not _player.is_playing():
		_player.play()
	is_playing = true
	playback_started.emit()


func pause() -> void:
	if not _open:
		return
	_player.paused = true
	is_playing = false
	playback_paused.emit()


func close() -> void:
	if _player.is_playing():
		_player.stop()
	_player.stream = null
	_player.paused = false
	_open = false
	is_playing = false


func is_open() -> bool:
	return _open


func seek_frame(_new_frame_nr: int) -> void:
	pass


func get_video_length_float() -> float:
	return _player.get_stream_length() if _open else 0.0


func get_current_playback_position_float() -> float:
	return _player.stream_position if _open else 0.0


func _set_enable_audio(value: bool) -> void:
	enable_audio = value
	_player.volume_db = 0.0 if value else -80.0


func _on_finished() -> void:
	if loop:
		_player.play()
		return
	is_playing = false
	video_ended.emit()
