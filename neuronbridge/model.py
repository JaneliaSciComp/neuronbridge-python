from typing import List, Union, Optional, Any
from pydantic import BaseModel
from devtools import debug

class NeuronImage(BaseModel):
    id: str
    libraryName: str
    publishedName: str
    imageURL: str
    thumbnailURL: str
    gender: str


class EMImage(NeuronImage):
    neuronType: str
    neuronInstance: str
    

class EMImageLookup(BaseModel):
    results: List[EMImage]
        

class LMImage(NeuronImage):
    slideCode: str
    objective: str
    anatomicalArea: str
    alignmentSpace: str
    channel: str
    mountingProtocol: str


class LMImageLookup(BaseModel):
    results: List[LMImage]


class Match(BaseModel):
    id: str
    publishedName: str
    libraryName: str
    alignmentSpace: str
    gender: str
    imageStack: Optional[str] = None
    mirrored: bool


class Files(BaseModel):
    ColorDepthMip: str
    SignalMipMaskedSkel: str
    ColorDepthMipSkel: str
    SignalMip: str
    SignalMipMasked: str


class PPPMatch(Match):
    pppRank: float
    pppScore: int
    # EM->LM
    slideCode: str
    objective: str
    mountingProtocol: str
    files: Files
    # TODO: this is a hack to get around the fact that PPP imagery is stored under the mask library name
    maskLibraryName: Optional[str] = None
    #anatomicalArea: str (currently missing!)
    # Unused
    #coverageScore: float
    #aggregateCoverage: float


class CDSMatch(Match):
    imageURL: str
    thumbnailURL: str
    searchablePNG: str
    sourceSearchablePNG: Optional[str] = None
    normalizedScore: float
    matchingPixels: int    
    # CDS LM->EM
    neuronType: Optional[str] = None
    neuronInstance: Optional[str] = None    
    # CDS EM->LM
    slideCode: Optional[str] = None
    objective: Optional[str] = None
    mountingProtocol: Optional[str] = None
    anatomicalArea: Optional[str] = None
    channel: Optional[str] = None
    # Unused
    #matchingRatio: float
    #gradientAreaGap: Optional[int] = None
    #highExpressionArea: Optional[int] = None
    #normalizedGapScore: Optional[float] = None


class PPPMatches(BaseModel):
    maskId: str
    maskPublishedName: str
    maskLibraryName: str
    neuronType: str
    neuronInstance: str
    results: List[PPPMatch]


class CDSMatches(BaseModel):
    maskId: str
    maskPublishedName: str
    maskLibraryName: str
    results: List[CDSMatch]
    maskImageStack: Optional[str] = None
    # Unused
    #maskImageURL: str
    #maskSampleRef: str
    #maskRelatedImageRefId: str
