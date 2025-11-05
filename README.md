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

### For NixOS with home-manager

Add the input to your `flake.nix`:
```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    hyprfloat = {
      url = "github:nevimmu/hyprfloat";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, home-manager, hyprfloat, ... }: {
    homeConfigurations.youruser = home-manager.lib.homeManagerConfiguration {
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      modules = [
        hyprfloat.homeManagerModules.default
        ./home.nix
      ];
    };
  };
}
```

Then in your `home.nix`:
```nix
{ config, pkgs, ... }:
{
  services.hyprfloat = {
    enable = true;
    autoStart = true;  # Automatically start with Hyprland
    
    settings = {
      terminal_classes = [
        "kitty"
        "alacritty"
        "org.kde.konsole"
        "com.mitchellh.ghostty"
        "foot"
      ];
      
      ignore_titles = [
        "cava"
        "btop"
        "htop"
      ];
      
      monitors = {
        "DP-1" = {
          width = 1818;
          height = 1023;
          offset = [ 0 0 ];
        };
        "HDMI-A-1" = {
          width = 767;
          height = 1364;
          offset = [ 0 0 ];
        };
      };
    };
  };
}
```

## Configuration
You can modify the terminals list and terminal width and height per monitors in `~/.config/hyprfloat/hyprfloat.json`

- terminal_classes: list of the terminals (or any app really) you want to auto float/tile. Use the app class
- ignore_titles: list of title that will be excluded. For example if you want your Cava that you spawn with that name not to float
- monitors: your monitors and the width and height floating windows will take, that's where you can customize it
	- offset: offset the floating window

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
			"height":1364,
			"offset": [0, 0]
		},
		"DP-1":{
			"width":1818,
			"height":1023,
			"offset": [0, 0]
		}
	}
}
```