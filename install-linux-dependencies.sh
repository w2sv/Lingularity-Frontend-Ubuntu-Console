package_installed()
{
  (dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -c "ok installed")
}

required_packages=("wmctrl" "xodotool")

for package in "${required_packages[@]}"
do
  if [ "$(package_installed "$package")" -eq 0 ];
  then
    sudo apt-get install "$package";
  fi
done