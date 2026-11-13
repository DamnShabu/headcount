//! The app updates itself from the files the release workflow publishes, by
//! name. Those names are written in three places -- the updater
//! (`update/channel.rs`), the workflow and the distribution package build --
//! and this checks that they agree.

use std::fs;
use std::path::PathBuf;

use rbxmgr_core::install::{Install, PackageFormat};
use rbxmgr_core::update::app::SUMS;
use rbxmgr_core::update::channel::asset_name;

fn repo_file(path: &str) -> String {
    let full = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(path);
    fs::read_to_string(&full).unwrap_or_else(|e| panic!("{}: {e}", full.display()))
}

/// The text with its version variables, in either syntax, as `version`.
fn with_version(text: &str, version: &str) -> String {
    text.replace("${{ env.VERSION }}", version).replace("${VERSION}", version)
}

#[test]
fn the_workflow_publishes_every_file_the_updater_downloads() {
    if std::env::consts::ARCH != "x86_64" {
        return;
    }
    let workflow = with_version(&repo_file(".github/workflows/release.yml"), "9.8.7");
    let packages = with_version(&repo_file("packaging/linux/build.sh"), "9.8.7");
    let name = |install: Install| asset_name(&install, "9.8.7").unwrap();

    for published in [name(Install::AppImage("/x".into())), name(Install::Flatpak)] {
        assert!(workflow.contains(&published), "release.yml never writes {published}");
    }
    for format in [PackageFormat::Deb, PackageFormat::Rpm, PackageFormat::Arch] {
        let built = name(Install::Package(format));
        assert!(packages.contains(&built), "packaging/linux/build.sh never writes {built}");
    }
    assert!(workflow.contains(&format!("> {SUMS}")), "release.yml writes no {SUMS}");
}

#[test]
fn each_package_tells_the_app_which_it_is() {
    let packages = repo_file("packaging/linux/build.sh");
    for format in ["deb", "rpm", "arch"] {
        assert!(PackageFormat::parse(format).is_some(), "the app does not know {format}");
        assert!(packages.contains(&format!("package {format} ")), "no {format} package is built");
    }
    assert!(packages.contains(&format!("{}=$format", rbxmgr_core::install::PACKAGE_VAR)));
}

/// Up to 0.13 the app was Roblox Manager, and those copies update from files
/// named `roblox-manager...`: the workflow publishes each file under that
/// name too, by swapping the prefix.
#[test]
fn copies_from_before_the_rename_still_find_their_file() {
    if std::env::consts::ARCH != "x86_64" {
        return;
    }
    let workflow = repo_file(".github/workflows/release.yml");
    assert!(
        workflow.contains(
            r#"for f in headcount[-_]*; do cp -- "$f" "roblox-manager${f#headcount}"; done"#
        ),
        "release.yml no longer publishes the names from before the rename"
    );
    let installs = [
        Install::AppImage("/x".into()),
        Install::Flatpak,
        Install::Package(PackageFormat::Deb),
        Install::Package(PackageFormat::Rpm),
        Install::Package(PackageFormat::Arch),
    ];
    for install in installs {
        let name = asset_name(&install, "9.8.7").unwrap();
        let rest = name.strip_prefix("headcount").unwrap_or_default();
        assert!(rest.starts_with(['-', '_']), "{name} is not matched by headcount[-_]*");
    }
}
