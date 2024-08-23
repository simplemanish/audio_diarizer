from dataclasses import dataclass
import requests
from time import sleep
import json
from urllib.parse import urlparse

# import video_blob
from utilities import video_blob
import os
from dotenv import load_dotenv
load_dotenv()


# Create a class with attributes that relate to VideoIndexer credentials
@dataclass
class VideoIndexer:
    subscription_key: str = os.getenv("VIDEO_INDEXER_SUB_KEY")
    account_id: str = os.getenv("VIDEO_INDEXER_ACC_ID")
    location: str = "TRIAL"  # change this if you have a paid subscription tied to a specific location

    @classmethod
    def get_access_token(cls):
        """
        Get an access token from the Video Indexer API. These expire every hour and are required in order to use the
        service.
        :return access_token: string.
        """

        url = "https://api.videoindexer.ai/Auth/{}/Accounts/{}/AccessToken?allowEdit=true".format(
            cls.location, cls.account_id
        )
        headers = {
            "Ocp-Apim-Subscription-Key": cls.subscription_key,
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            access_token = response.json()
            return access_token
        else:
            print("[*] Error when calling video indexer API.")
            print("[*] Response : {} {}".format(response.status_code, response.reason))

    @classmethod
    def send_to_video_indexer(cls, video_url, video_id, access_token):
        """
        Send a video to be analysed by video indexer.
        :param video_id: string, identifier for the video..
        :param video_url: string, public url for the video.
        :param access_token: string, required to use the API.
        :return video_indexer_id: string, used to access video details once indexing complete.
        """

        # parsed_url = urlparse(video_url)
        # if not parsed_url.scheme or not parsed_url.netloc:
        #     raise Exception(f'Invalid video URL: {video_url}')
        # print("parsed_url :",parsed_url)
        # Set request headers and url
        headers = {
            "Content-Type": "multipart/form-data",
            "Ocp-Apim-Subscription-Key": cls.subscription_key,
        }
        # files = {
        #     'file': (f'<{video_url}>.mp4', open('<video_url>.mp4', 'rb')),
        # }
        from urllib.parse import quote

        # s = video_url
        s = quote(video_url.encode("utf-8"))
        video_indexer_url = (
            "https://api.videoindexer.ai/{}/Accounts/{}/Videos?name={}&privacy=Private&indexingPreset=Advanced&accessToken={}&sendSuccessEmail=True&streamingPreset=NoStreaming&videoUrl={}"
        ).format(cls.location, cls.account_id, video_id, access_token, s)
        print("video_indexer_new_url :",video_indexer_url)
        # Make request and catch errors
        response = requests.post(url=video_indexer_url, headers=headers)
        if response.status_code == 200:
            video_indexer_id = response.json()["id"]
            return video_indexer_id
        # If the access token has expired get a new one
        if response.status_code == 401:
            print("[*] Access token has expired, retrying with new token.")
            access_token = cls.get_access_token()
            video_indexer_new_url = """https://api.videoindexer.ai/{}/Accounts/{}/Videos?name={}&privacy=Private&videoUrl={}&accessToken={}&sendSuccessEmail=True&streamingPreset=NoStreaming""".format(
                cls.location,
                cls.account_id,
                video_id,
                video_url,
                access_token,
            )
            
            response = requests.post(url=video_indexer_new_url, headers=headers)
            if response.status_code == 200:
                video_indexer_id = response.json()["id"]
                return video_indexer_id
            else:
                print("[*] Error after retrying.")
                print(
                    "[*] Response : {} {}".format(response.status_code, response.reason)
                )
        # If you are sending too many requests
        if response.status_code == 429:
            print("[*] Throttled for sending too many requests.")
            time_to_wait = response.headers["Retry-After"]
            print("[*] Retrying after {} seconds".format(time_to_wait))
            sleep(int(time_to_wait))
            response = requests.post(url=video_indexer_url, headers=headers)
            if response.status_code == 200:
                video_indexer_json_output = response.json()
                return video_indexer_json_output
            else:
                print("[*] Error after retrying following throttling.")
                print(
                    "[*] Response : {} {}".format(response.status_code, response.reason)
                )
        else:
            print("[*] Error when calling video indexer API.")
            print("[*] Response : {} {} {}".format(response.status_code, response.reason, response.content))

    @classmethod
    def get_indexed_video_data(cls, video_id):
        """
        Retrieves data on the video after analysis from the Video Indexer API.
        :param video_id: string, unique identifier for the indexed video.
        :param access_token: string, required to use the API.
        :return video_indexer_json_output: JSON, analysed video data.
        """
        segments =[]
        access_token = cls.get_access_token()
        # Set request headers and url
        headers = {
            "Ocp-Apim-Subscription-Key": cls.subscription_key,
        }
        url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/{}/Index?includedInsights=Transcript&accessToken={}".format(
            cls.location, cls.account_id, video_id, access_token
        )

        # Make request and handle unauthorized error
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            video_indexer_json_output = response.json()
            if video_indexer_json_output["state"] == "Processed":
                video_diarization = video_indexer_json_output["videos"][0]["insights"]["transcript"]
                for i in range(len(video_diarization)):
                    segments.append({
                    'speaker_id': video_diarization[i]["speakerId"],
                    'text': video_diarization[i]["text"],
                    'start_time': video_diarization[i]["instances"][0]["start"],
                    'end_time': video_diarization[i]["instances"][0]["end"]
                    })
                    print("Segments : ",segments)
                    # print("Speaker_ID :",video_diarization[i]["speakerId"])
                    # print("Text :",video_diarization[i]["text"])
                diarize_text = ""
                last_speaker_id = None

                for segment in segments:
                    if last_speaker_id is None:
                        # For the first segment, start with "Guest-X:"
                        diarize_text += f"Speaker{segment['speaker_id']} ({segment['start_time']}-{segment['end_time']}): {segment['text']}"
                    elif segment['speaker_id'] == last_speaker_id:
                        # If the current speaker is the same as the last one, append the text
                        diarize_text += " " + segment['text']
                    else:
                        # If the speaker changes, add a new entry with "Guest-X:"
                        diarize_text += f"\nSpeaker{segment['speaker_id']} ({segment['start_time']}-{segment['end_time']}): {segment['text']}"

                    last_speaker_id = segment['speaker_id']
                print("diarize_text :",diarize_text)
                return diarize_text
            # print("Length of video_diarization :",len(video_diarization))
            # with open("video_indexer_response.json", "w") as f:
            #     json.dump(indexer_response, f)
        else:
            print("[*] Video has not finished processing")
            return video_indexer_json_output
        

        # If the access token has expired get a new one
        if response.status_code == 401:
            print("[*] Access token has expired, retrying with new token.")
            access_token = cls.get_access_token()
            video_indexer_new_url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/{}/Index?accessToken={}".format(
                cls.location, cls.account_id, video_id, access_token
            )
            
            response = requests.post(url=video_indexer_new_url, headers=headers)
            if response.status_code == 200:
                video_indexer_json_output = response.json()
                return video_indexer_json_output
            else:
                print("[*] Error after retrying.")
                print(
                    "[*] Response : {} {}".format(response.status_code, response.reason, response.content)
                )
        else:
            print("[*] Error when calling video indexer API.")
            print("[*] Response : {} {}".format(response.status_code, response.reason))
    
    def create_prompt_content(cls, video_id, access_token):
        """
        Retrieves data on the video after analysis from the Video Indexer API.
        :param video_id: string, unique identifier for the indexed video.
        :param access_token: string, required to use the API.
        :return video_indexer_json_output: JSON, analysed video data.
        """

        # Set request headers and url
        headers = {
            "Ocp-Apim-Subscription-Key": cls.subscription_key,
        }
        # https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos/{videoId}/PromptContent[?modelName][&promptStyle][&accessToken]
        url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/{}/PromptContent?accessToken={}".format(
            cls.location, cls.account_id, video_id, access_token
        )

        # Make request and handle unauthorized error
        response = requests.post(url=url, headers=headers)
        if response.status_code == 200:
            video_indexer_json_output = response.json()
            return video_indexer_json_output

        # If the access token has expired get a new one
        if response.status_code == 401:
            print("[*] Access token has expired, retrying with new token.")
            access_token = cls.get_access_token()
            video_indexer_new_url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/{}/Index?accessToken={}".format(
                cls.location, cls.account_id, video_id, access_token
            )
            
            response = requests.post(url=video_indexer_new_url, headers=headers)
            if response.status_code == 200:
                video_indexer_json_output = response.json()
                return video_indexer_json_output
            else:
                print("[*] Error after retrying.")
                print(
                    "[*] Response : {} {} {}".format(response.status_code, response.reason, response.content)
                )
        else:
            print("[*] Error when calling video indexer API.")
            print("[*] Response : {} {} {}".format(response.status_code, response.reason,  response.content))

    def get_prompt_content(cls, video_id, access_token):
            """
            Retrieves data on the video after analysis from the Video Indexer API.
            :param video_id: string, unique identifier for the indexed video.
            :param access_token: string, required to use the API.
            :return video_indexer_json_output: JSON, analysed video data.
            """

            # Set request headers and url
            headers = {
                "Ocp-Apim-Subscription-Key": cls.subscription_key,
            }
            
            url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/{}/PromptContent?accessToken={}".format(
                cls.location, cls.account_id, video_id, access_token
            )
            print("url :",url)

            # Make request and handle unauthorized error
            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                video_indexer_json_output = response.json()
                return video_indexer_json_output

            # If the access token has expired get a new one
            if response.status_code == 401:
                print("[*] Access token has expired, retrying with new token.")
                access_token = cls.get_access_token()
                video_indexer_new_url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/{}/PromptContent?accessToken={}".format(
                    cls.location, cls.account_id, video_id, access_token
                )
                
                response = requests.post(url=video_indexer_new_url, headers=headers)
                if response.status_code == 200:
                    video_indexer_json_output = response.json()
                    return video_indexer_json_output
                else:
                    print("[*] Error after retrying.")
                    print(
                        "[*] Response : {} {} {}".format(response.status_code, response.reason, response.content)
                    )
            else:
                print("[*] Error when calling video indexer API.")
                print("[*] Response : {} {} {}".format(response.status_code, response.reason, response.content))

    def get_video_list(cls):
        access_token = cls.get_access_token()
        headers = {
            "Ocp-Apim-Subscription-Key": cls.subscription_key,
        }
        # https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos[?createdAfter][&createdBefore][&pageSize][&skip][&partitions][&accessToken]
        url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/?accessToken={}".format(
            cls.location, cls.account_id, access_token
        )

        # Make request and handle unauthorized error
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            video_indexer_json_output = response.json()
            video_id =[]
            video_name =[]
            video_state =[]
            for i in video_indexer_json_output["results"]:
                video_id.append(i["id"])
                video_name.append(i["name"])
                video_state.append(i["state"])
            print(video_id)
            print(video_name)
            
            video_list_json ={}
            video_list_json = [
                {
                "video_id":video_id,
                "video_name":video_name,
                "video_state" : video_state
                }for video_id, video_name, video_state in zip (video_id,video_name,video_state)
            ]
            print(video_list_json)
            return video_list_json

        # If the access token has expired get a new one
        if response.status_code == 401:
            print("[*] Access token has expired, retrying with new token.")
            access_token = cls.get_access_token()
            video_indexer_new_url = "https://api.videoindexer.ai/{}/Accounts/{}/Videos/?accessToken={}".format(
                cls.location, cls.account_id, access_token
            )
            
            response = requests.post(url=video_indexer_new_url, headers=headers)
            if response.status_code == 200:
                video_indexer_json_output = response.json()
                video_id =[]
                video_name =[]
                video_state =[]
                for i in video_indexer_json_output["results"]:
                    video_id.append(i["id"])
                    video_name.append(i["name"])
                    video_state.append(i["state"])
                print(video_indexer_json_output)
                print(video_name)
                print(video_state)
                video_list_json ={}
                video_list_json = [
                    {
                    "video_id":video_id,
                    "video_name":video_name,
                    "video_state" : video_state
                    }for video_id, video_name, video_state in zip (video_id,video_name,video_state)
                ]
                print(video_list_json)
                return video_list_json
            else:
                print("[*] Error after retrying.")
                print(
                    "[*] Response : {} {}".format(response.status_code, response.reason, response.content)
                )
        else:
            print("[*] Error when calling video indexer API.")
            print("[*] Response : {} {}".format(response.status_code, response.reason))



if __name__ == "__main__":
    vi = VideoIndexer()

    # To send videos
    my_access_token = vi.get_access_token()
    # print("my_access_token :",my_access_token)
    # video_list = vi.get_video_list()
    # print("video_list:",video_list)

    file_name = "video.mp4"
    storage_video_url=video_blob.uploadToBlobStorage("resources/video.mp4","video.mp4")
    print("storage_video_url :",storage_video_url)
    response_id = vi.send_to_video_indexer(
        # video_url=".//resources//video2.mp4",
        video_url=storage_video_url,
        video_id=file_name,
        access_token=my_access_token,
    )
    print("response_id :",response_id)

    # To retrieve videos
    # indexer_response = vi.get_indexed_video_data(
    #     video_id="x9xfnfbvad"
    # )
    # print("indexer_response :",indexer_response)
    # if indexer_response["state"] == "Processed":
    #     video_diarization = indexer_response["videos"][0]["insights"]["transcript"]
    #     for i in range(len(video_diarization)):
    #         print("Speaker_ID :",video_diarization[i]["speakerId"])
    #         print("Text :",video_diarization[i]["text"])
    #     print("Length of video_diarization :",len(video_diarization))
    #     with open("video_indexer_response.json", "w") as f:
    #         json.dump(indexer_response, f)
    # else:
    #     print("[*] Video has not finished processing")

    # prompt_content = vi.get_prompt_content(
    #     video_id="4e55sh4c9m", access_token=my_access_token
    # )

    # print("prompt content :",prompt_content)