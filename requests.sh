# # GET
# curl \
#     -X GET \
#     localhost:8000/personnel/all/ | jq

# GET
curl \
    -X GET \
    localhost:8000/personnel/professor/3/

# # POST
# curl \
#     --data '{
#     "first_name": "Posting",
#     "last_name":"Desde Curl",
#     "career":""
# }' \
#     -X POST \
#     localhost:8000/personnel/professor/add/

# # PUT
# curl \
#     --data '{
#     "first_name": "Editanto",
#     "last_name":"Desde new view",
#     "career":"Hacker"
# }' \
#     -X PUT \
#     localhost:8000/personnel/professor/edit/6/


# # DELETE
# curl \
#     -X DELETE \
#     localhost:8000/personnel/professor/delete/2/
