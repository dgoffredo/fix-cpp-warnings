
def rewrite(fin, fout, rewrites, alreadySorted=False):
    if not alreadySorted:
        def selectOffset(tup):
            return tup[0]
        rewrites = sorted(rewrites, key=selectOffset)

    fin.seek(0) 
    FROM_CURRENT_POSITION = 1
    for offset, oldLen, replacement in rewrites:
        fout.write(fin.read(offset - fin.tell())) # catch up
        fout.write(replacement)
        fin.seek(oldLen, FROM_CURRENT_POSITION) # skip the old

    fout.write(fin.read()) # the rest of it

