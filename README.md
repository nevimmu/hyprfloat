# Hyprfloat

Float the terminal in empty workspace

## Installation and use

### From the AUR
```bash
yay -S hyprfloat
```

### From source
```bash
$ git clone https://github.com/nevimmu/hyprfloat
$ cd hyprfloat
$ pipx install .
```

and add `exec-once = hyprfloat` to your `hyprland.conf`

## Configuration
You can modify the terminals list and terminal width and height per monitors in `~/.config/hyprfloat/hyprfloat.json`

- terminal_classes: list of the terminals (or any app really) you want to auto float/tile. Use the app class
- ignore_titles: list of title that will be excluded. For example if you want your Cava that you spawn with that name not to float
- monitors: your monitors and the width and height floating windows will take, that's where you can customize it

Example configuration:
```json
{
	"terminal_classes":[
		"kitty",
		"alacritty",
		"org.kde.konsole",
		"com.mitchellh.ghostty"
	],
	"ignore_titles":[
		"cava",
		"btop"
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