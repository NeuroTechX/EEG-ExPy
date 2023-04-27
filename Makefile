build:
	pip install .

test:
	pytest

typecheck:
	# Exclude visual_cueing due to errors
	python -m mypy --exclude 'examples/visual_cueing'

docs:
	cd doc && make html

clean:
	cd doc && make clean

install-deps-apt:
	sudo apt-get update  # update archive links

	# xvfb is a dependency to create a virtual display
	# libgtk-3-dev is a requirement for wxPython
	# freeglut3-dev is a requirement for a wxPython dependency
	# portaudio19-dev *might* be required to import psychopy on Ubuntu
	# pulseaudio *might* be required to actually run the tests (on PsychoPy import)
	# libpulse-dev required to build pocketsphinx (speech recognition dependency of psychopy)
	# libsdl2-dev required by psychopy
	# libnotify4 is so we can have the libnotify.so module used in wxPython working
	sudo apt-get -y install xvfb libgtk-3-dev freeglut3-dev portaudio19-dev libpulse-dev pulseaudio libsdl2-dev libnotify4
	
	# configure dynamic links
	sudo ldconfig
	
	UPDATED_LIBPATH=$(sudo find / -name libnotify.so)
	LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$UPDATED_LIBPATH

install-deps-wxpython:
	# Install wxPython wheels since they are distribution-specific and therefore not on PyPI
	# See: https://wxpython.org/pages/downloads/index.html
	pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython
