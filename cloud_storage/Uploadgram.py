import UploadgramPyAPI


class Uploadgram:
    @staticmethod
    async def upload(path_to_file: str):
        try:
            up_file = UploadgramPyAPI.NewFile(path_to_file)
            response: dict = up_file.upload()
            return response
        except UploadgramPyAPI.UploadgramConnectionError as e:
            print(e.args)
            return e.args

    @staticmethod
    async def delete(uploaded_file_data: dict[str, str, str]):
        file_id = str(uploaded_file_data.get('url')).split('/')[-1]
        delete_key = uploaded_file_data.get('delete_key')
        try:
            up_file = UploadgramPyAPI.File(file_id, delete_key)
            response: dict = up_file.delete()
            return response
        except UploadgramPyAPI.UploadgramConnectionError as e:
            print(e.args)
            return e.args