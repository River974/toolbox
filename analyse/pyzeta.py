#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyzeta.py
# #cf



#=================================
# Import statements
#=================================

import os
import re
import glob
import pandas as pd
from collections import Counter
import treetaggerwrapper
#import itertools
import shutil
import pygal


#=================================
# Functions
#=================================


def make_filelist(DataFolder, MetadataFile, Contrast): 
    """
    Based on the metadata, create two lists of files, each from one group.
    The category to check and the two labels are found in Contrast.
    """
    with open(MetadataFile, "r") as InFile: 
        Metadata = pd.DataFrame.from_csv(InFile, sep=";")
        OneMetadata = Metadata[Metadata[Contrast[0]].isin([Contrast[1]])]
        TwoMetadata = Metadata[Metadata[Contrast[0]].isin([Contrast[2]])]
        OneList = list(OneMetadata.loc[:,"idno"])
        TwoList = list(TwoMetadata.loc[:,"idno"])
        #print(OneList, TwoList)
        print("---", len(OneList), len(TwoList), "texts")
        return OneList, TwoList


def merge_text(DataFolder, List, File): 
    """
    Merge all texts from one group into one large text file.
    Creates less loss when splitting.
    """
    with open(File, 'wb') as OutFile:
        PathList = [DataFolder+Item+".txt" for Item in List]
        for File in PathList:
            try:
                with open(File, 'rb') as ReadFile:
                    shutil.copyfileobj(ReadFile, OutFile)
            except: 
                print("exception.")


def read_file(File):
    """
    Read one text file per partition.
    """
    FileName,Ext = os.path.basename(File).split(".")
    with open(File, "r") as InFile: 
        Text = InFile.read()
    #print(Text)
    return Text, FileName


def prepare_text(Text, Mode, Pos, Forms, Stoplist):
    """
    Takes a text in string format and transforms and filters it. 
    Makes it lowercase, splits into tokens, discards tokens of length 1.
    Alternatively, applies POS-tagging and selection of specific POS.
    Returns a list. 
    """
    if Mode == "plain": 
        Prepared = Text.lower()
        Prepared = re.split("\W", Prepared)
        Prepared = [Token for Token in Prepared if len(Token) > 1]    
    if Mode == "tag": 
        Tagger = treetaggerwrapper.TreeTagger(TAGLANG="fr")
        print("---tagging")
        Tagged = Tagger.tag_text(Text)
        print("---done tagging")
        Prepared = []
        for Line in Tagged:
            Line = re.split("\t", Line)
            if len(Line) == 3: 
            #print(len(Line), Line)
                if Forms == "lemmas":
                    Prepared.append(Line[2])
                elif Forms == "words": 
                    Prepared.append(Line[0])
                elif Forms == "pos": 
                    Prepared.append(Line[1])
        Prepared = [Token for Token in Prepared if len(Token) > 1]    
    if Mode == "sel": 
        Tagger = treetaggerwrapper.TreeTagger(TAGLANG="fr")
        print("---tagging")
        Tagged = Tagger.tag_text(Text)
        print("---done tagging")
        Prepared = []
        for Line in Tagged:
            Line = re.split("\t", Line)
            if len(Line) == 3: 
            #print(len(Line), Line)
                if Line[1][0:2] in Pos:
                    if Forms == "lemmas":
                        Prepared.append(Line[2])
                    elif Forms == "words": 
                        Prepared.append(Line[0])
                    elif Forms == "pos": 
                        Prepared.append(Line[1])
    if Mode == "posbigrams": 
        Tagger = treetaggerwrapper.TreeTagger(TAGLANG="fr")
        print("---tagging")
        Tagged = Tagger.tag_text(Text)
        print("---done tagging")
        Prepared = []
        for i in range(0,len(Tagged)-1): 
            Line = re.split("\t", Tagged[i])
            NextLine = re.split("\t", Tagged[i+1])
            Prepared.append(Line[1]+"-"+NextLine[1])
    if Mode == "wordbigrams": 
        Text = Text.lower()
        Text = re.split("\W", Text)
        Text = [Token for Token in Text if len(Token) > 1]    
        Prepared = []
        for i in range(0,len(Text)-1): 
            Prepared.append(Text[i]+"-"+Text[i+1])
    Prepared = [Item.lower() for Item in Prepared if Item not in Stoplist]
    print(Prepared[0:50])
    return Prepared 


def save_seg(Seg, SegFile, SegsFolder): 
    """
    Function to save one segment to disk for sequential reading.
    """
    with open(SegsFolder+SegFile, "w") as OutFile: 
        OutFile.write(Seg)


def segment_text(Prepared, SegLength, Filename, SegsFolder):
    """
    Splits the whole text document into segments of fixed length; discards rest. 
    Also, reduces each segment to the set of different words in the segment. 
    """
    NumSegs = int(len(Prepared)/SegLength)
    #print("text length (prepared)", len(Prepared))
    #print("number of segments", NumSegs)
    for i in range(0,NumSegs): 
        Seg = Prepared[i*SegLength:(i+1)*SegLength]
        #print(len(Seg))
        Seg = list(set(Seg))
        #print(len(Seg))
        Seg = "\t".join(Seg)
        SegFile = Filename+"{:04d}".format(i)+".txt"
        save_seg(Seg, SegFile, SegsFolder)
    return NumSegs


def get_types(OnePrepared, TwoPrepared, Threshold):
    """
    Merges all prepared text and extracts the types with their frequency (Counter). 
    Filters the list of types based on their frequency and length in chars.
    A high frequency threshold may speed things up but information is lost. 
    """
    Types = Counter()
    Types.update(OnePrepared)
    Types.update(TwoPrepared)
    #print(Types)
    Types = {k:v for (k,v) in Types.items() if v > Threshold and len(k) > 1}
    #print(Types)
    #Set all values to zero.
    Types = dict.fromkeys(Types, 0)
    #print("number of types in collection (filtered)", len(list(Types.keys())))
    #print(list(itertools.islice(Types.items(), 0, 5)))
    return Types
    
       
def check_types(SegsPath, Types, NumSegs):
    """
    For each text segment in one group: 
    1. Read the file and split on the tab
    2. For each Type in the list of all Types, check whether it exists in the file.
    3. If it does, increase the value in the dict for this type by one.
    At the end, divide all dict values by the number of segments. 
    """
    Types = dict.fromkeys(Types, 0)
    for SegFile in glob.glob(SegsPath):    # TODO: this part is really slow ###
        #print("SegFile:", SegFile)
        with open(SegFile, "r") as InFile: 
            Seg = InFile.read()
            Seg = re.split("\t", Seg)
            for Type in Types:       
                if Type in Seg:
                    Types[Type] = Types[Type]+1
    Props = {k: v / NumSegs for k, v in Types.items()}
    return Props
                    

def get_zetas(Types, OneProps, TwoProps, ZetaFile):
    """
    Perform the actual Zeta calculation.
    Zeta = Proportion in Group One + (1-Proportion in Group 2) -1
    """
    AllResults = []
    for Type in Types:
        try:
            OneProp = OneProps[Type]
        except: 
            OneProp = 0
        try:
            TwoProp = TwoProps[Type]
        except: 
            TwoProp = 0
        Zeta = OneProp + (1-TwoProp) -1
        Result = {"type":Type, "one-prop":OneProp, "two-prop":TwoProp, "zeta":Zeta}
        AllResults.append(Result)
    AllResults = pd.DataFrame(AllResults)
    AllResults = AllResults[["type", "one-prop", "two-prop", "zeta"]]
    AllResults = AllResults.sort_values("zeta", ascending=False)
    print(AllResults.head(10))
    print(AllResults.tail(10))
    with open(ZetaFile, "w") as OutFile: 
        AllResults.to_csv(OutFile)


#=================================
# Main coordinating function
#=================================

def zeta(WorkDir, InputFolder, 
         MetadataFile, Contrast,
         DataFolder,
         SegLength, Threshold,
         Mode, Pos, Forms, Stoplist):
    """
    Python implementation of Craig's Zeta. 
    Status: proof-of-concept quality.
    """
    # Generate necessary file and folder names
    OneFile = DataFolder + Contrast[1] + ".txt"
    TwoFile = DataFolder + Contrast[2] + ".txt"
    SegsFolder = DataFolder + Contrast[1]+"-"+Contrast[2]+"_segs-of-"+str(SegLength)+"-"+Mode+"-"+Forms+"-"+str(Pos[0])+"/"
    ZetaFile = DataFolder + Contrast[1]+"-"+Contrast[2]+"_zeta-scores_segs-of-"+str(SegLength)+"-"+Mode+"-"+Forms+"-"+str(Pos[0])+".csv"
    # Create necessary folders
    if not os.path.exists(DataFolder):
        os.makedirs(DataFolder)
    if not os.path.exists(SegsFolder):
        os.makedirs(SegsFolder)
    # Generate list of files for the two groups
    print("--generate list of files")
    OneList, TwoList = make_filelist(InputFolder, MetadataFile, Contrast)
    # Merge text files into two input files
    print("--merge_text (one and two)")
    merge_text(InputFolder, OneList, OneFile)
    merge_text(InputFolder, TwoList, TwoFile)
    # Load both text files       
    print("--read_file (one and two)")
    OneText, OneFileName = read_file(OneFile)
    TwoText, TwoFileName = read_file(TwoFile)
    # Prepare both text files
    print("--prepare_text (one)")
    OnePrepared = prepare_text(OneText, Mode, Pos, Forms, Stoplist)
    print("--prepare_text (two)")
    TwoPrepared = prepare_text(TwoText, Mode, Pos, Forms, Stoplist)
    # Segment both text files
    print("--segment_text (one and two)")
    NumSegsOne = segment_text(OnePrepared, SegLength, OneFileName, SegsFolder)
    NumSegsTwo = segment_text(TwoPrepared, SegLength, TwoFileName, SegsFolder)
    print("  Number of segments (one, two)", NumSegsOne, NumSegsTwo)
    # Extract the list of selected types 
    print("--get_types (one)")
    Types = get_types(OnePrepared, TwoPrepared, Threshold)
    print("  Number of types", len(list(Types.keys())))
    # Check in how many segs each type is (one)
    print("--check_types (one)")
    OneProps = check_types(SegsFolder+Contrast[1]+"*.txt", Types, NumSegsOne)
    # Extract the list of selected types (repeat)
    print("--get_types (two)")
    Types = get_types(OnePrepared, TwoPrepared, Threshold)
    # Check in how many segs each type is (two)
    print("--check_types (two)")
    TwoProps = check_types(SegsFolder+Contrast[2]+"*.txt", Types, NumSegsTwo)
    # Calculate zeta for each type
    print("--get_zetas")
    get_zetas(Types, OneProps, TwoProps, ZetaFile)






#=================================
# Visualize zeta data
#=================================

zeta_style = pygal.style.Style(
  background='white',
  plot_background='white',
  font_family = "FreeSans",
  title_font_size = 20,
  legend_font_size = 16,
  label_font_size = 12,
  colors=["#1d91c0","#225ea8","#253494","#081d58", "#071746"])



def get_zetadata(ZetaFile, NumWords): 
    with open(ZetaFile, "r") as InFile: 
        ZetaData = pd.DataFrame.from_csv(InFile)
        #print(ZetaData.head())
        ZetaData.drop(["one-prop", "two-prop"], axis=1, inplace=True)
        ZetaData.sort_values("zeta", ascending=False, inplace=True)
        ZetaDataHead = ZetaData.head(NumWords)
        ZetaDataTail = ZetaData.tail(NumWords)
        ZetaData = ZetaDataHead.append(ZetaDataTail)
        ZetaData = ZetaData.reset_index(drop=True)
        #print(ZetaData)
        return ZetaData


def plot_zetadata(ZetaData, Contrast, PlotFile, NumWords): 
    plot = pygal.HorizontalBar(style=zeta_style,
                               print_values=False,
                               print_labels=True,
                               show_legend=False,
                               range=(-1,1),
                               title="Kontrastive Analyse mit Zeta",
                               x_title=Contrast[2]+" _____ vs _____ "+Contrast[1],
                               y_title="Je "+str(NumWords)+" Worte pro Sammlung"
                               )
    for i in range(len(ZetaData)):
        if ZetaData.iloc[i,1] > 0.8: 
            Color = "#00cc00"
        if ZetaData.iloc[i,1] > 0.7: 
            Color = "#14b814"
        if ZetaData.iloc[i,1] > 0.6: 
            Color = "#29a329"
        elif ZetaData.iloc[i,1] > 0.5: 
            Color = "#3d8f3d"
        elif ZetaData.iloc[i,1] > 0: 
            Color = "#4d804d"
        elif ZetaData.iloc[i,1] < -0.8: 
            Color = "#0066ff"
        elif ZetaData.iloc[i,1] < -0.7: 
            Color = "#196be6"
        elif ZetaData.iloc[i,1] < -0.6: 
            Color = "#3370cc"
        elif ZetaData.iloc[i,1] < -0.5: 
            Color = "#4d75b3"
        elif ZetaData.iloc[i,1] < 0: 
            Color = "#60799f"
        else: 
            Color = "DarkGrey"
        plot.add(ZetaData.iloc[i,0], [{"value":ZetaData.iloc[i,1], "label":ZetaData.iloc[i,0], "color":Color}])
    plot.render_to_file(PlotFile)


def plot_zeta(ZetaFile,
              NumWords,
              Contrast,
              PlotFile): 
    print("--plot_zeta")
    ZetaData = get_zetadata(ZetaFile, NumWords)
    plot_zetadata(ZetaData, Contrast, PlotFile, NumWords)

















