with open('data.json', 'r') as file:
    data = json.load(file)

build_id = data.get('build_id')
project_name = data.get('project_name')
version = data.get('version')
author = data.get('author')
release_date = data.get('release_date')
post_build_int = data.get('post_build_int')
build_ID_dot = data.get('build_ID.')

print(build_id)
print(project_name)
print(version)
print(author)
print(release_date)
print(post_build_int)
print(build_ID_dot)