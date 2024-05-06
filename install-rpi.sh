sudo apt-get install -y build-essential zlib1g-dev uuid-dev liblzma-dev lzma-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev < /dev/null
sudo apt install -y libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev python3-tk tk-dev

# install python
new_version="3.10.2"
file="Python-${new_version}.tar.xz"
url="https://www.python.org/ftp/python/${new_version}/${file}"

echo "Downloading Python ${new_version}"
wget "${url}"
echo "Decompressing file"
tar -Jxf "${file}" < /dev/null

cd Python-${new_version}
echo "Prepare the source for the installation"
./configure --enable-optimizations --prefix=/usr < /dev/null
make -j$(nproc) < /dev/null
echo "(Install the new Python version $new_version)"
sudo make install -j$(nproc)
sudo ./configure --with-tcltk-includes='-I/usr/include -I/usr/include/tcl' --with-tcltk-libs='-L/usr/lib -ltcl -ltk' --enable-optimizations

echo "Let's cleanup!"
cd ..
rm -rf "Python-$new_version"
rm -r "${file}"

python3.10 -m venv venv
source venv/bin/activate

echo "Let's install PIP"
sudo apt install -y python3-pip < /dev/null

echo "updating pip..."
python -m pip install --upgrade pip

pip install -r ./requirements.txt

git clone --recurse-submodules https://github.com/SeleniumHQ/selenium.git
cd selenium/rust
curl https://sh.rustup.rs -sSf > install-rust.sh
chmod +x ./install-rust.sh
./install-rust.sh -y
. "$HOME/.cargo/env"
cargo build

sudo cp target/debug/selenium-manager /usr/bin/selenium-manager
export SE_MANAGER_PATH=/usr/bin/selenium-manager
echo "export SE_MANAGER_PATH=/usr/bin/selenium-manager" >> $HOME/.bashrc

echo "Let's cleanup!"
cd ../..
rm -rf "Python-$new_version"
rm -r "${file}"
rm -rf "selenium"
