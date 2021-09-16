Project setup:

1. install dependencies from requirements.txt using pip
2. run django management command 'project_init' to setup DB, initial data, env variables etc.
3. create superuser for django admin
4. for users to be able to upload images assign them a profile - ThumbUser model
5. API endpoints:
    thumbs/upload_img/
    thumbs/list_img/
    thumbs/get_img_temp_link/?img=img_id&exp=exp_seconds