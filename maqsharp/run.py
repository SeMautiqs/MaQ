import sys, maude
maude.init(advise=True)
for f in sys.argv[1:]:
    maude.load(f)
