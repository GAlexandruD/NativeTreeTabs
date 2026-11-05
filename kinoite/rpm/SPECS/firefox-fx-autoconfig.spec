Name:           firefox-fx-autoconfig
Version:        0
Release:        1.gitdfdab56%{?dist}
Summary:        fx-autoconfig loader hook for Fedora Firefox (enables userChrome .uc.js scripts)
License:        MPL-2.0
URL:            https://github.com/MrOtherGuy/fx-autoconfig
Source0:        config.js
Source1:        config-prefs.js
Source2:        LICENSE
BuildArch:      x86_64
Requires:       firefox

%description
Installs the two program-side files of fx-autoconfig (commit dfdab56) into
the Firefox install directory. The loader only activates for profiles that
contain chrome/utils/chrome.manifest; other profiles are unaffected.

%install
install -Dm0644 %{SOURCE0} %{buildroot}/usr/lib64/firefox/config.js
install -Dm0644 %{SOURCE1} %{buildroot}/usr/lib64/firefox/defaults/pref/config-prefs.js
install -Dm0644 %{SOURCE2} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
/usr/lib64/firefox/config.js
/usr/lib64/firefox/defaults/pref/config-prefs.js
%license %{_licensedir}/%{name}/LICENSE
