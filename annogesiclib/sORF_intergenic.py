import os
import sys
from annogesiclib.gff3 import Gff3Parser

def get_type(inter, gffs):
    utr5 = False
    utr3 = False
    for gff in gffs:
        if (gff.seq_id == inter["strain"]) and \
           (gff.strand == inter["strand"]):
            if gff.strand == "+":
                if inter["end"] + 1 == gff.start:
                    utr5 = True
                if inter["start"] - 1 == gff.end:
                    utr3 = True
            else:
                if inter["end"] + 1 == gff.start:
                    utr3 = True
                if inter["start"] - 1 == gff.end:
                    utr5 = True
    if utr3 and utr5:
        inter["source"] = "interCDS"
    elif utr3:
        inter["source"] = "3utr"
    elif utr5:
        inter["source"] = "5utr"
    else:
        inter["source"] = "intergenic"

def read_gff(gff_file, tran_file):
    trans = []
    gffs = []
    gh = open(gff_file)
    for entry in Gff3Parser().entries(gh):
        if (entry.feature == "CDS") or \
           (entry.feature == "rRNA") or \
           (entry.feature == "tRNA") or \
           (entry.feature == "sRNA"):
            gffs.append(entry)
    th = open(tran_file)
    for entry in Gff3Parser().entries(th):
        trans.append(entry)
    gffs = sorted(gffs, key=lambda k: (k.seq_id, k.start))
    trans = sorted(trans, key=lambda k: (k.seq_id, k.start))
    gh.close()
    th.close()
    return gffs, trans

def compare_tran_cds(trans, gffs):
    inters = []
    for tran in trans:
        poss = [{"start": tran.start, "end": tran.end}]
        for pos in poss:
            exclude = False
            for gff in gffs:
                if (tran.seq_id == gff.seq_id) and \
                   (tran.strand == gff.strand):
                    if (gff.start <= pos["start"]) and \
                       (gff.end >= pos["start"]) and \
                       (gff.end < pos["end"]):
                        pos["start"] = gff.end + 1
                    elif (gff.start > pos["start"]) and \
                         (gff.start <= pos["end"]) and \
                         (gff.end >= pos["end"]):
                        pos["end"] = gff.start - 1
                    elif (gff.start <= pos["start"]) and \
                         (gff.end >= pos["end"]):
                        exclude = True
                        break
                    elif (gff.start > pos["start"]) and \
                         (gff.end < pos["end"]):
                        poss.append({"start": gff.end + 1, "end": pos["end"]})
                        pos["end"] = gff.start - 1
            if not exclude:
                inters.append({"strain": tran.seq_id, "strand": tran.strand,
                               "start": pos["start"], "end": pos["end"]})
    return inters

def get_intergenic(gff_file, tran_file, out_file, utr_detect):
    gffs, trans = read_gff(gff_file, tran_file)
    inters = compare_tran_cds(trans, gffs)
    num = 0
    out = open(out_file, "w")
    for inter in inters:
        get_type(inter, gffs)
        name = '%0*d' % (5, num)
        if inter["source"] != "intergenic":
            source = "UTR_derived"
            if utr_detect:
                attribute_string = ";".join(
                       ["=".join(items) for items in (["ID", "sorf" + str(num)],
                       ["Name", "sORF_" + name],
                       ["UTR_type", inter["source"]])])
        else:
            source = "intergenic"
            attribute_string = ";".join(
                   ["=".join(items) for items in (
                   ["ID", "sorf" + str(num)], ["Name", "sORF_" + name])])
        if ((source == "UTR_derived") and (utr_detect)) or \
           (source == "intergenic"):
            out.write("\t".join([str(field) for field in [
                        inter["strain"], source, "sORF", str(inter["start"]),
                        str(inter["end"]), ".", inter["strand"], ".",
                        attribute_string]]) + "\n")
        num += 1
    out.close()
