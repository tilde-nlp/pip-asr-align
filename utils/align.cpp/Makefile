ifdef DEBUG
	OPT = -O0 --debug -g -ggdb
	OPT_D = -g
else
	OPT = -O2
	OPT_D = 
endif

all:

OBJFILES = align.o

CXXFLAGS += -std=c++11 $(OPT)

LDFLAGS += $(OPT_D)

BINFILES = align

all: $(BINFILES)

$(BINFILES): $(OBJFILES)

.o:
	$(CXX) -o $@ $(EXTRA_LDLIBS) $(LDLIBS) $(LDFLAGS) \
	  $@.o

clean: 
	-rm -f *.o *.a $(BINFILES)
 


