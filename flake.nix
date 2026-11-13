{
  description = "Headcount: several Roblox accounts, launched into one server";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    # Bundles a derivation's closure into one AppImage (userns-chroot AppRun).
    nix-appimage = {
      url = "github:ralismark/nix-appimage";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    nix-appimage,
  }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system} = {
      default = self.packages.${system}.headcount;
      headcount = import ./package.nix {inherit pkgs;};
      # Its name before the rename, for configs that still ask for it.
      roblox-manager = self.packages.${system}.headcount;
      cordial-mujo = import ./cordial/package.nix {inherit pkgs;};
      headcount-appimage = import ./appimage.nix {
        inherit pkgs nix-appimage;
        inherit (nixpkgs) lib;
        inherit (self.packages.${system}) headcount;
      };
      flatpak-cargo-generator = import ./packaging/flatpak/cargo-generator.nix {inherit pkgs;};
    };

    # The Rust workspace (crates/): toolchain plus the GTK4/libadwaita
    # headers the app crate links against.
    devShells.${system}.default = pkgs.mkShell {
      packages = with pkgs; [cargo rustc clippy rustfmt rust-analyzer pkg-config gtk4 libadwaita];
    };

    nixosModules.default = ./module.nix;
  };
}
