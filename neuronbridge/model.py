from typing import List, Union, Optional, Any, Dict
from enum import Enum
from pydantic import BaseModel, Field

class Gender(str, Enum):
    male = 'm'
    female = 'f'


class AnatomicalRegion(BaseModel):
    """
    """
    label: str = Field(description="")
    value: str = Field(description="")
    disabled: Optional[bool] = Field(description="")


class DataConfig(BaseModel):
    """
    """
    prefixes: Dict[str, str] = Field(description="")
    anatomicalRegions: List[AnatomicalRegion] = Field(description="")


class Files(BaseModel):
    """
    Files associated with a NeuronImage or Match. These are either absolute URLs (e.g. starting with a protocol like http://) or relative paths. For relative paths, the first component should be replaced with its corresponding base URL from the DataConfig.
    """
    ColorDepthMip: Optional[str] = Field(description="The CDM of the image. For PPPM, this is the best matching channel of the matching LM stack and called 'LM - Best Channel CDM' in the NeuronBridge GUI.")
    ColorDepthMipThumbnail: Optional[str] = Field(description="The thumbnail of the ColorDepthMip, if available.")
    ColorDepthMipMatched: Optional[str] = Field(description="PPPM-only. The CDM of the best matching channel of the matching LM stack. 'LM - Best Channel CDM' in the NeuronBridge GUI.")
    ColorDepthMipSkel: Optional[str] = Field(description="PPPM-only. The CDM of the best matching channel with the matching LM segmentation fragments overlaid. 'LM - Best Channel CDM with EM overlay' in the NeuronBridge GUI.")
    SignalMip: Optional[str] = Field(description="PPPM-only. The full MIP of all channels of the matching sample. 'LM - Sample All-Channel CDM' in the NeuronBridge GUI.")
    SignalMipMasked: Optional[str] = Field(description="PPPM-only. LM signal content masked with the matching LM segmentation fragments. 'PPP Mask' in the NeuronBridge GUI.")
    SignalMipMaskedSkel: Optional[str] = Field(description="PPPM-only. LM signal content masked with the matching LM segmentation fragments, overlaid with the EM skeleton. 'PPP Mask with EM Overlay' in the NeuronBridge GUI.")
    SignalMipExpression: Optional[str] = Field(description="MCFO-only. A representative CDM image of the full expression of the line.")
    VisuallyLosslessStack: Optional[str] = Field(description="LMImage-only. An H5J 3D image stack of all channels of the LM image.")
    AlignedBodySWC: Optional[str] = Field(description="EMImage-only, A 3D SWC skeleton of the EM body in the alignment space.")
    AlignedBodyOBJ: Optional[str] = Field(description="EMImage-only. A 3D OBJ representation of the EM body in the alignment space.")

class NeuronImage(BaseModel):
    """
    A color depth image containing neurons. 
    """
    id: str = Field(description="The unique identifier for this image.")
    libraryName: str = Field(description="Name of the image library containing this image.")
    publishedName: str = Field(description="Published name for the contents of this image. This is not a unique identifier.")
    alignmentSpace: str = Field(description="Alignment space to which this image was registered.")
    gender: Gender = Field(description="Gender of the sample imaged.")
    files: Files = Field(description="Files associated with the image.")


class EMImage(NeuronImage):
    """
    A color depth image containing a neuron body reconstructed from EM imagery.
    """
    neuronType: Optional[str] = Field(description="Neuron type name from neuPrint")
    neuronInstance: Optional[str] = Field(description="Neuron instance name from neuPrint")


class EMImageLookup(BaseModel):
    """
    Top level collection returned by the EMImage lookup API.
    """
    results: List[EMImage] = Field(description="List of EM images matching the query.")
        

class LMImage(NeuronImage):
    """
    A color depth image of a single channel of an LM image stack.
    """
    slideCode: str = Field(description="Unique identifier for the sample that was imaged.")
    objective: str = Field(description="Magnification of the microscope objective used to imaged this image.")
    # TODO: this is only temporarily optional until #2px2113 is fixed
    mountingProtocol: Optional[str] = Field(description="Description of the protocol used to mount the sample for imaging.")
    anatomicalArea: str = Field(description="Anatomical area of the sample that was imaged.")
    channel: Optional[int] = Field(description="Channel index within the full LM image stack. PPPM matches the entire stack and therefore this is blank.")


class LMImageLookup(BaseModel):
    """
    Top level collection returned by the LMImage lookup API.
    """
    results: List[LMImage] = Field(description="List of LM images matching the query.")


class Match(BaseModel):
    """
    Putative matching between two NeuronImages.
    """
    image: NeuronImage = Field(description="The NeuronImage that was matched.")
    mirrored: bool = Field(description="Indicates whether the target image was found within a mirrored version of the matching image.")
    def get_score(self):
        pass


class PPPMatch(Match):
    """
    A PPPMatch is a match generated by the PPPM algorithm between an EMImage and a LMImage.
    """
    pppRank: float = Field(description="Fractional rank reported by the PPPM algorithm. It's generally better to use the index of the image in the results.")
    pppScore: int = Field(description="Match score reported by the PPPM algorithm.")


class CDSMatch(Match):
    """
    A CDSMatch is a match generated by the CDS algorithm between an EMImage and a LMImage.
    """
    normalizedScore: float = Field(description="Match score reported by the matching algorithm")
    matchingPixels: int = Field(description="Number of matching pixels reported by the CDS algorithm")


class PPPMatches(BaseModel):
    """
    The results of PPPM matching run on a NeuronImage.
    """
    inputImage: NeuronImage = Field(description="Input image to the PPPM matching algorithm.")
    results: List[PPPMatch] = Field(description="List of other images matching the input image.")


class CDSMatches(BaseModel):
    """
    The results of CDM matching run on a NeuronImage.
    """
    inputImage: NeuronImage = Field(description="Input image to the CDS matching algorithm.")
    results: List[CDSMatch] = Field(description="List of other images matching the input image.")



def to_lookup(json_obj):
    """
    """
    if "slideCode" in json_obj['results'][0]:
        return LMImageLookup(**json_obj)
    else:
        return EMImageLookup(**json_obj)


def to_matches(json_obj):
    """
    """
    if "slideCode" in json_obj['results'][0]:
        return LMImageLookup(**json_obj)
    else:
        return EMImageLookup(**json_obj)
    return Matches(**json_obj)



