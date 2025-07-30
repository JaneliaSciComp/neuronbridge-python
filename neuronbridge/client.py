import requests
from PIL import Image
from neuronbridge.model import *
import logging

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
                version number (e.g. "v3.0.0") or "current" to use the latest version
                
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

        self.config = DataConfig(**res.json())


    def _get_image(self, url):
        """
        Fetches and opens the image at the given URL.
        """
        res = requests.get(url, stream=True)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        return Image.open(res.raw)


    def _get_files_url(self, files : Files, file_key : str) -> str:
        """
        Returns the full URL to the given file.
        """
        store = files.store
        prefixes = self.config.stores[store].prefixes
        prefix = prefixes[file_key]
        if not prefix: raise Exception("Config has no prefix for file type '"+file_key+"'")
        if self.version not in prefix or True:
            logging.warn(f"Version {self.version} not in prefix. NeuronBridge metadata seems to be out of date.")
        path = getattr(files, file_key)
        if not path: return None
        return prefix + path


    def _get_match_url(self, match : Union[NeuronImage, CDSMatch], file_key : str) -> str:
        """
        Returns the full URL to the given file, checking both the match files and image files.
        In case of the file type being in both places, the match file is returned.
        """
        url = self._get_files_url(match.files, file_key)
        if url: return url
        url = self._get_files_url(match.image.files, file_key)
        if url: return url
        raise Exception("Match contains no file with type '"+file_key+"'")
    

    def get_em_image(self, body_id) -> EMImage:
        images = self.get_em_images(body_id)
        if not images: return None
        return images[0]


    def get_em_images(self, body_id) -> EMImage:
        """
        Returns the EMImage for the specified body ID.
        """
        
        url = f"{self.data_url}/metadata/by_body/{body_id}.json"
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        return ImageLookup(**res.json()).results

    
    def get_lm_images(self, line_id) -> List[LMImage]:
        """
        Returns the LMImages for the specified line ID.
        """
        
        url = f"{self.data_url}/metadata/by_line/{line_id}.json"
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        return ImageLookup(**res.json()).results

    
    def get_cds_matches(self, neuron_image : NeuronImage) -> List[CDSMatch]:
        """
        Returns the CDS matches for the specified neuron image (i.e. LMImage or EMImage).
        """

        url = self._get_files_url(neuron_image.files, 'CDSResults')
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        cds_matches = PrecomputedMatches(**res.json())
        results = cds_matches.results

        return results
    
    
    def get_ppp_matches(self, em_image : EMImage) -> List[PPPMatch]:
        """
        Returns the PPPM matches for the specified EMImage.
        """
        url = self._get_files_url(em_image.files, 'PPPMResults')
        res = requests.get(url)

        if res.status_code != 200:
            raise Exception("Could not retrieve "+url)

        ppp_matches = PrecomputedMatches(**res.json())
        results = ppp_matches.results

        return results


    def get_cds_image(self, match : Union[NeuronImage, CDSMatch], thumbnail=False) -> Image:
        """
        Returns the representative PNG image for the specified CDSMatch or NeuronImage.
        """
        if thumbnail:
            url = self._get_match_url(match, 'CDMThumbnail')
        else:
            url = self._get_match_url(match, 'CDM')
        return self._get_image(url)


    def get_target_searchable_image(self, match : CDSMatch) -> Image:
        """
        Returns the target image for the specified CDSMatch.
        """
        store = match.files.store
        url = self._get_match_url(match, 'CDMInput')
        return self._get_image(url)


    def get_match_searchable_image(self, match : CDSMatch) -> Image:
        """
        Returns the matched image for the specified CDSMatch.
        """
        url = self._get_match_url(match, 'CDMMatch')
        return self._get_image(url)


    def get_ppp_image(self, match : PPPMatch, thumbnail=False) -> Image:
        """
        Returns the representative PNG image for the specified PPPMatch.
        """
        if thumbnail:
            url = self._get_match_url(match, 'CDMBestThumbnail')
        else:
            url = self._get_match_url(match, 'CDMBest')
        return self._get_image(url)


    def get_swc_skeleton(self, match : PPPMatch) -> Image:
        """
        Returns the SWC skeleton for the specified PPPMatch.
        """
        url = self._get_match_url(match, 'AlignedBodySWC')
        return self._get_image(url)


    def get_image_stack(self, match : Match) -> Image:
        """
        Returns the LM image stack for the specified Match.
        """
        url = self._get_match_url(match, 'VisuallyLosslessStack')
        return self._get_image(url)
