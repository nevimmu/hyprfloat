{
	description = "Float the terminal in empty workplace - A Hyprland window management tool";

	inputs = {
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
		flake-utils.url = "github:numtide/flake-utils";
		home-manager = {
			url = "github:nix-community/home-manager";
			inputs.nixpkgs.follows = "nixpkgs";
		};
	};

	outputs = { self, nixpkgs, flake-utils, home-manager }:
		flake-utils.lib.eachDefaultSystem (system:
			let
				pkgs = nixpkgs.legacyPackages.${system};
				
				hyprfloat = pkgs.python3Packages.buildPythonApplication {
					pname = "hyprfloat";
					version = "0.4.2";
					
					src = ./.;
					
					pyproject = true;
					
					nativeBuildInputs = with pkgs.python3Packages; [
						setuptools
					];
					
					# No runtime dependencies since it only uses standard library
					propagatedBuildInputs = [ ];
					
					# Skip tests since there are none in the repository
					doCheck = false;
					
					meta = with pkgs.lib; {
						description = "Float the terminal in empty workspace for Hyprland";
						homepage = "https://github.com/nevimmu/hyprfloat";
						license = licenses.mit;
						maintainers = [ ];
						platforms = platforms.linux; # Hyprland is Linux-only
						mainProgram = "hyprfloat";
					};
				};
			in
			{
				packages = {
					default = hyprfloat;
					hyprfloat = hyprfloat;
				};

				apps = {
					default = flake-utils.lib.mkApp {
						drv = hyprfloat;
						name = "hyprfloat";
					};
					hyprfloat = flake-utils.lib.mkApp {
						drv = hyprfloat;
						name = "hyprfloat";
					};
				};

				devShells.default = pkgs.mkShell {
					buildInputs = with pkgs; [
						python3
						python3Packages.setuptools
						commitizen
						pipx
					];
					
					shellHook = ''
						export PATH="$HOME/.local/bin:$PATH"
						echo "Hyprfloat development environment"
						echo "Run 'pipx install -e .' to install in development mode"
					'';
				};
			}
		) // {
			# Home Manager module
			homeManagerModules.default = { config, lib, pkgs, ... }:
				with lib;
				let
					cfg = config.services.hyprfloat;
					
					# Convert the configuration to JSON
					configJson = pkgs.writeText "hyprfloat.json" (builtins.toJSON cfg.settings);
				in
				{
					options.services.hyprfloat = {
						enable = mkEnableOption "hyprfloat window management service";
						
						package = mkOption {
							type = types.package;
							default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
							description = "The hyprfloat package to use";
						};
						
						settings = mkOption {
							type = types.attrs;
							default = {
								terminal_classes = [
									"kitty"
									"alacritty"
									"org.kde.konsole"
									"com.mitchellh.ghostty"
								];
								ignore_titles = [ ];
								monitors = { };
							};
							description = ''
								Configuration for hyprfloat. This will be written to ~/.config/hyprfloat/hyprfloat.json.
								
								- terminal_classes: List of terminal window classes to manage
								- ignore_titles: List of window titles to exclude from management
								- monitors: Per-monitor configuration for floating window dimensions and offset
							'';
							example = literalExpression ''
								{
									terminal_classes = [ "kitty" "alacritty" ];
									ignore_titles = [ "cava" "btop" ];
									monitors = {
										"HDMI-A-1" = {
											width = 767;
											height = 1364;
											offset = [ 0 0 ];
										};
										"DP-1" = {
											width = 1818;
											height = 1023;
											offset = [ 0 0 ];
										};
									};
								}
							'';
						};
						
						autoStart = mkOption {
							type = types.bool;
							default = true;
							description = "Whether to automatically start hyprfloat with Hyprland";
						};
					};
					
					config = mkIf cfg.enable {
						home.packages = [ cfg.package ];
						
						# Create the config file
						xdg.configFile."hyprfloat/hyprfloat.json" = {
							source = configJson;
						};
						
						# Add to Hyprland config if autoStart is enabled
						wayland.windowManager.hyprland = mkIf cfg.autoStart {
							settings = {
								exec-once = [ "${cfg.package}/bin/hyprfloat" ];
							};
						};
						
						# Alternative: create a systemd user service for manual control
						systemd.user.services.hyprfloat = {
							Unit = {
								Description = "Hyprfloat window management service";
								PartOf = [ "graphical-session.target" ];
								After = [ "graphical-session.target" ];
							};
							
							Service = {
								Type = "simple";
								ExecStart = "${cfg.package}/bin/hyprfloat";
								Restart = "on-failure";
								RestartSec = "5s";
								Environment = [
									"PATH=${pkgs.hyprland}/bin:$PATH"
								];
							};
							
							Install = {
								WantedBy = [ "graphical-session.target" ];
							};
						};
					};
				};
			
			# Home Manager module alias for convenience
			homeManagerModules.hyprfloat = self.homeManagerModules.default;
		};
}