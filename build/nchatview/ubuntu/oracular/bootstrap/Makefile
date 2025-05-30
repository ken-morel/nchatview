CFLAGS=$(shell /usr/bin/python3.12-config --cflags --embed)
LDFLAGS=$(shell /usr/bin/python3.12-config --ldflags --embed)

all: nchatview

pyversion.h:
	python3.12 -c "import sys; print(f'#define PY_TAG \"{sys.version_info.major}.{sys.version_info.minor}\"')" > pyversion.h

nchatview: main.c pyversion.h
	gcc -o nchatview $^ $(CFLAGS) $(LDFLAGS) -fPIE

clean:
	rm -rf ../nchatview-0.0.1/usr/bin
	rm -f nchatview pyversion.h

install: all
	mkdir -p ../nchatview-0.0.1/usr/bin
	cp nchatview ../nchatview-0.0.1/usr/bin

.PHONY: all clean install
