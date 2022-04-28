from typing import List, Union, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

class Gender(str, Enum):
    male = 'm'
    female = 'f'

class NeuronImage(BaseModel):
    """
    A color depth image containing neurons. 
    """
    id: str = Field(description="The unique identifier for this image.")
    libraryName: str = Field(description="Name of the image library containing this image.")
    publishedName: str = Field(description="Published name for the contents of this image. This is not a unique identifier.")
    imageURL: str = Field(description="Path to a PNG version of the image. Relative to imageryBaseURL in the config.json.")
    thumbnailURL: str = Field(description="Path of a PNG thumbnail of the image. Relative to thumbnailsBaseURLs in the config.json.")
    gender: Gender = Field(description="Gender of the sample imaged.")


class EMImage(NeuronImage):
    """
    A color depth image containing a neuron body reconstructed from EM imagery.
    """
    neuronType: str = Field(description="Neuron type name from neuPrint")
    neuronInstance: str = Field(description="Neuron instance name from neuPrint")
    #alignmentSpace: str (currently missing)    


class EMImageLookup(BaseModel):
    """
    Top level collection returned by the EMImage lookup API.
    """
    results: List[EMImage] = Field(description="List of EM images matching the query.")
        

class LMImage(NeuronImage):
    """
    A color depth image of a single channel of an LM image stack.
    """
    alignmentSpace: str = Field(description="Alignment space to which this image was registered.")
    slideCode: str = Field(description="Unique identifier for the sample that was imaged.")
    objective: str = Field(description="Magnification of the microscope objective used to imaged this image.")
    mountingProtocol: str = Field(description="Description of the protocol used to mount the sample for imaging.")
    anatomicalArea: str = Field(description="Anatomical area of the sample that was imaged.")
    channel: str = Field(description="Channel index within the full LM image stack.")


class LMImageLookup(BaseModel):
    """
    Top level collection returned by the LMImage lookup API.
    """
    results: List[LMImage] = Field(description="List of LM images matching the query.")


class Match(BaseModel):
    """
    Putative matching between two NeuronImages.
    """
    id: str = Field(description="Unique identifier of the matching image.")
    publishedName: str = Field(description="Published name for the contents of the matching image.")
    libraryName: str = Field(description="Name of the image library containing the matching image.")
    alignmentSpace: str = Field(description="Alignment space to which the matching image was registered.")
    gender: str = Field(description="Gender of the sample represented in the matching image.")
    imageStack: Optional[str] = Field(description="URL of the full LM image stack of the matching image.")
    mirrored: bool = Field(description="Indicates whether the target image was found within a mirrored version of the matching image.")
    maskLibraryName: Optional[str] = Field(description="This is just a hack to get around the fact that PPP imagery is stored under the mask library name.", exclude=True)

class Files(BaseModel):
    """
    Files associated with a NeuronImage or Match.
    """
    ColorDepthMip: str = Field(description="PPPM-only. Relative path to the CDM of the best matching channel of the matching LM stack. 'LM - Best Channel CDM' in the NeuronBridge GUI.")
    ColorDepthMipSkel: str = Field(description="PPPM-only. Relative path to CDM of the best matching channel with the matching LM segmentation fragments overlaid. 'LM - Best Channel CDM with EM overlay' in the NeuronBridge GUI.")
    SignalMip: str = Field(description="PPPM-only. Relative path to the full MIP of all channels of the matching sample. 'LM - Sample All-Channel CDM' in the NeuronBridge GUI.")
    SignalMipMasked: str = Field(description="PPPM-only. Relative path to an image showing LM signal content masked with the matching LM segmentation fragments. 'PPP Mask' in the NeuronBridge GUI.")
    SignalMipMaskedSkel: str = Field(description="PPPM-only. Relative path an image showing LM signal content masked with the matching LM segmentation fragments, overlaid with the EM skeelton. 'PPP Mask with EM Overlay' in the NeuronBridge GUI.")


class PPPMatch(Match):
    """
    A PPPMatch is a match generated by the PPPM algorithm between an EMImage and a LMImage.
    """
    pppRank: float = Field(description="Fractional rank reported by the PPPM algorithm. It's generally better to use the index of the image in the results.")
    pppScore: int = Field(description="Match score reported by the PPPM algorithm.")
    # EM->LM
    slideCode: str = Field(description="Unique identifier for the sample that was imaged.")
    objective: str = Field(description="Magnification of the microscope objective used to imaged this image.")
    mountingProtocol: str = Field(description="Description of the protocol used to mount the sample for imaging.")
    files: Files = Field(description="Files characterizing the match.")
    #anatomicalArea: str (currently missing!)
    # Unused fields present in the 2.4.0 JSON
    #coverageScore: float
    #aggregateCoverage: float


class CDSMatch(Match):
    """
    A CDSMatch is a match generated by the CDS algorithm between an EMImage and a LMImage.
    """
    imageURL: str = Field(description="Path to a PNG version of the image, relative to imageryBaseURL in the config.json.")
    thumbnailURL: str = Field(description="Path of a PNG thumbnail of the image, relative to thumbnailsBaseURLs in the config.json.")
    searchablePNG: str = Field(description="Path to a PNG version of the image that was actually matched. This is the same as imageURL if the image was not segmented or otherwise processed prior to searching.")
    sourceSearchablePNG: Optional[str] = Field(description="Path to a PNG version of the target image that was actually matched.")
    normalizedScore: float = Field(description="Match score reported by the matching algorithm")
    matchingPixels: int = Field(description="Number of matching pixels reported by the CDS algorithm")
    # CDS LM->EM
    neuronType: Optional[str] = Field(description="Neuron type name from neuPrint")
    neuronInstance: Optional[str] = Field(description="Neuron instance name from neuPrint")
    # CDS EM->LM
    slideCode: Optional[str] = Field(description="Unique identifier for the sample that was imaged.")
    objective: Optional[str] = Field(description="Magnification of the microscope objective used to imaged this image.")
    mountingProtocol: Optional[str] = Field(description="Description of the protocol used to mount the sample for imaging.")
    anatomicalArea: Optional[str] = Field(description="Anatomical area of the sample that was imaged.")
    channel: Optional[str] = Field(description="Channel index within the full LM image stack.")
    # Unused fields present in the 2.4.0 JSON
    #matchingRatio: float
    #gradientAreaGap: Optional[int] = None
    #highExpressionArea: Optional[int] = None
    #normalizedGapScore: Optional[float] = None


class PPPMatches(BaseModel):
    """
    The results of a PPPM algorithm run on an EMImage.
    """
    maskId: str = Field(description="Unique identifier of the target image.")
    maskPublishedName: str = Field(description="Published name for the contents of the target image.")
    maskLibraryName: str = Field(description="Name of the image library containing the target image.")
    neuronType: Optional[str] = Field(description="Neuron type name from neuPrint")
    neuronInstance: Optional[str] = Field(description="Neuron instance name from neuPrint")
    results: List[PPPMatch] = Field(description="List of PPPM matches.")


class CDSMatches(BaseModel):
    """
    The results of a CDS algorithm run on an EMImage or LMImage.
    """
    maskId: str = Field(description="Unique identifier of the target image.")
    maskPublishedName: str = Field(description="Published name for the contents of the target image.")
    maskLibraryName: str = Field(description="Name of the image library containing the target image.")
    maskImageStack: Optional[str] = Field(description="URL of the full LM image stack for the target image.")
    results: List[CDSMatch] = Field(description="List of CDS matches.")
    # Unused fields present in the 2.4.0 JSON
    #maskImageURL: str
    #maskSampleRef: str
    #maskRelatedImageRefId: str

