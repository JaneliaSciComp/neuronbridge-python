import requests
from PIL import Image
from neuronbridge.model import *

class Client:
    def __init__(self, data_bucket="janelia-neuronbridge-data-prod", version="current"):
        """
        Client constructor. 
        
        When the client is created, it retrieves the configuration for the specified version. 
        If ``version='current'`` then the latest version is first retrieved from NeuronBridge.
        
        Args:
            data_bucket:
                name of the S3 bucket containing the NeuronBridge metadata
            version:
                version number (e.g. "v2.4.0") or "current" to use the latest version
                
        """

        data_url_prefix = f"https://{data_bucket}.s3.us-east-1.amazonaws.com"

        if version == "current":
            url = data_url_prefix + "/current.txt"
            res = requests.get(url)
            if res.status_code != 200:
                raise Exception("Could not retrieve "+url)
            self.version = res.text.rstrip()
        else:
            self.version = version
            
        self.data_url = f"{data_url_prefix}/{self.version}"
        url = self.data_url + "/config.json"
        res = requests.get(url)
        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        self.config = res.json()


    def get_em_image(self, body_id) -> EMImage:
        
        url = f"{self.data_url}/metadata/by_body/{body_id}.json"
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        images = EMImageLookup(**res.json()).results
        if not images: return None
        return images[0]

    
    def get_lm_images(self, line_id) -> List[LMImage]:
        
        url = f"{self.data_url}/metadata/by_line/{line_id}.json"
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        return LMImageLookup(**res.json()).results

    
    def get_cds_matches(self, neuron_image : NeuronImage) -> List[CDSMatch]:

        url = f"{self.data_url}/metadata/cdsresults/{neuron_image.id}.json"
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        return CDSMatches(**res.json()).results
    
    
    def get_ppp_matches(self, em_image : EMImage) -> List[PPPMatch]:

        url = f"{self.data_url}/metadata/pppresults/{em_image.publishedName}.json"
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        ppp_matches = PPPMatches(**res.json())
        results = ppp_matches.results
        # TODO: this is a hack to get around the fact that PPP imagery is stored under the mask library name
        for result in results:
            result.maskLibraryName = ppp_matches.maskLibraryName
        return results

    def _get_image(self, url):

        res = requests.get(url, stream=True)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        return Image.open(res.raw)


    def get_cds_image(self, match : Union[NeuronImage, CDSMatch], thumbnail=False) -> Image:
        if thumbnail:
            url = self.config['thumbnailsBaseURLs'] + "/" + match.thumbnailURL
        else:
            url = self.config['imageryBaseURL'] + "/" + match.imageURL
        return self._get_image(url)


    def get_ppp_image(self, match : PPPMatch) -> Image:
        url = f"{self.config['pppImageryBaseURL']}/{match.alignmentSpace}/{match.maskLibraryName}/{match.files.ColorDepthMip}"
        return self._get_image(url)


    def get_swc_skeleton(self, match : PPPMatch) -> Image:
        url = f"{self.config['swcBaseURL']}/{match.publishedName}.swc"
        return self._get_image(url)


    def get_image_stack(self, match : Match) -> Image:
        return self._get_image(match.imageStack)
