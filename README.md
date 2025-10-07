# Hyprfloat

Float the terminal in empty workspace

## Installation and use

```bash
$ git clone https://github.com/nevimmu/hyprfloat
$ cd hyprfloat
$ pipx install .
```

and add `exec-once = hyprfloat` to your `hyprland.conf`

## Configuration
You can modify the terminals list and terminal width and height per monitors in `~/.config/hyprfloat/hyprfloat.json`

```json
{
	"terminals":[
		"kitty",
		"alacritty",
		"org.kde.konsole",
		"com.mitchellh.ghostty"
	],
	"monitors":{
		"HDMI-A-1":{
			"width":767,
			"height":1364
		},
		"DP-1":{
			"width":1818,
			"height":1023
		}
	}
}
```