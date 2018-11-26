# muspy API documentation

A draft specification of the muspy API.

Use `https://muspy.com/api/1/<resource>`. Unless otherwise noted, requests must
be authenticated using HTTP basic authentication.

Default output format is json, you can change it to xml by adding `?format=xml`
to the request URL. POST/PUT parameters should be sent as form data.

## Resources

### artist/\<mbid>

**GET**: artist info, **no authentication required**
    
Example:

    GET https://muspy.com/api/1/artist/87cf6aa6-a005-445b-8920-1c5b3fdfbfaa

    {
        "mbid": "87cf6aa6-a005-445b-8920-1c5b3fdfbfaa",
        "name": "Montreal",
        "disambiguation": "German Punk Rock band",
        "sort_name": "Montreal"
    }

### artists/\<userid>[/\<mbid>]

**All operations require authentication.**

**GET**: list of all artists for the user (mbid, name, sort_name,
  disambiguation)
  
Example:
    
    GET https://muspy.com/api/1/artists/johndoe

    [
        {
            "mbid": "d9bebadd-c071-4a83-b2b2-4ef277ea6a7d",
            "name": "59 Times the Pain",
            "disambiguation": "",
            "sort_name": "59 Times the Pain"
        },
        ...
    ]
  
**PUT**: follow a new artist, return the artist info. `<mbid>` is required
  unless `import` is non-empty.
  
    * import: instead of adding artists by mbid, import them. Only 'last.fm'
      is supported for now.
    * username: Last.fm user name
    * count: max 500
    * period: one of ['overall', '12month', '6month', '3month', '7day']
    
Example:

    PUT https://muspy.com/api/1/artists/johndoe/d7bd0fad-2f06-4936-89ad-60c5b6ada3c1

    {
        "mbid": "d7bd0fad-2f06-4936-89ad-60c5b6ada3c1",
        "name": "No Use for a Name",
        "disambiguation": "",
        "sort_name": "No Use for a Name"
    }
    
**DELETE** unfollow an artist, `<mbid>` is required

Example:

    DELETE https://muspy.com/api/1/artists/johndoe/d7bd0fad-2f06-4936-89ad-60c5b6ada3c1
    
Returns status code 204 if ok. 400 if not.

### release/\<mbid>
     
**GET**: release group info (artist, mbid, name, type, date), **no authentication required**

Example:

    GET https://muspy.com/api/1/release/00c3d89f-d0f3-42a5-aede-1e4db29fa683
    
    {
        "date": "2009-09-10",
        "mbid": "00c3d89f-d0f3-42a5-aede-1e4db29fa683",
        "type": "Album",
        "name": "In This Light and on This Evening",
        "artists": [
            {
                "mbid": "0efe858c-89e5-4e47-906a-356fa953fd6e",
                "name": "Editors",
                "disambiguation": "",
                "sort_name": "Editors"
            }
        ]
    }

### releases[/\<userid>]
     
**GET**: list of release groups, sorted by release date. If `<userid>` is not
      supplied, the call will return release groups starting from today for all
      artists and the user's release type filters won't apply. **no authentication required**.
      
        * limit: max 100
        * offset
        * mbid: optional artist mbid, if set filter by this artist.
        * since: return releases fetched after the specified mbid, cannot be
          combined with offset or mbid.

### user[/\<userid>]

**All operations require authentication.**

**GET**: return user info and settings of the authenticated user.

TODO: Disallow fetching info about arbitrary users.

Example:

    GET https://muspy.com/api/1/user/johndoe

    {
        "notify_compilation": true,
        "notify_live": true,
        "notify_album": true,
        "userid": "johndoe",
        "notify_other": true,
        "notify_single": true,
        "notify": true,
        "notify_remix": true,
        "notify_ep": true,
        "email": "john@doe.localhost"
    }
    

**POST**: create a new user, no auth
* email
* password
* activate: 1 to send an activation email

Example:

    POST https://muspy.com/api/1/user/
    
        Content-Disposition: form-data; name="email"

    john@doe.localhost
    
    Content-Disposition: form-data; name="password"
    
        L8hqEsaRPJbQMfpMiVzGYwMs]pVtLRwU78WqvhxNo
    
    Content-Disposition: form-data; name="activate"
    
        1

    {
        "notify_compilation": true,
        "notify_live": true,
        "notify_album": true,
        "userid": "johndoe",
        "notify_other": true,
        "notify_single": true,
        "notify": true,
        "notify_remix": true,
        "notify_ep": true,
        "email": "john@doe.localhost"
    }

**PUT**: update user info and settings


Example:

    PUT https://muspy.com/api/1/user/johndoe
    
    Content-Disposition: form-data; name="notify_compilation"

    false
    
    Content-Disposition: form-data; name="notify_live"
    
    false

    {
        "notify_compilation": false,
        "notify_live": false,
        "notify_album": true,
        "userid": "johndoe",
        "notify_other": true,
        "notify_single": true,
        "notify": true,
        "notify_remix": true,
        "notify_ep": true,
        "email": "john@doe.localhost"
    }

**DELETE**: delete the user and all their data

Example: 

    DELETE https://muspy.com/api/1/user/johndoe
    

## Notes

The API is quite new and will probably change in the coming weeks. I suggest
that you [subscribe][0] to [the blog][1] where such changes will be announced.

If you are going to use the API for commercial purposes (e.g. selling CDs or ads
on the pages where the main content is pulled from the muspy API) I expect a 50%
revenue share. Alternatively, you can donate these money to [MusicBrainz][2],
[Django][3] or [FreeBSD][4]. If you are a [free software][5] project, feel free
to use the API as you see fit.

[0]: http://kojevnikov.com/muspy.xml
[1]: http://kojevnikov.com/tag/muspy.html
[2]: http://metabrainz.org/donate/
[3]: https://www.djangoproject.com/foundation/donate/
[4]: http://www.freebsdfoundation.org/donate/
[5]: http://www.gnu.org/philosophy/free-sw.html
