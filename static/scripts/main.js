var filenames = [];
var base_url = "http://localhost:5055"

function progress_bar(filename) {
    $('#upload-wrapper').hide();
    $('#status').append(
        $('<div>', { 'class': 'progress-bar-wrapper', 'data-filename': filename })
            .append($('<div>', { 'class': 'progress-bar-text px-0 py-2 very-small regular mt-2' })
                .append($('<span>', { 'class': '' }).html('Uploading '))
                .append($('<span>', { 'class': 'bold' }).html(filename))
                .append($('<span>', { 'class': '' }).html('...'))
            )
            .append($('<div>', { 'class': 'rounded bg-lightgrey border-custom overflow-hidden mb-3' })
                .append($('<div>', { 'class': 'progress-bar bg-primary text-center py-1 rounded-right text-nowrap' })
                    .html('0%')
                    .css('width', '0%')
                )
            )
    );
}

function range(n) {
    const R = []
    for (let i = 1; i < n+1; i++) R.push(i)
    return R
}

// Upload Reads to Amazon S3 Bucket
function upload_file() {

    // Get files
    var files = $('#fileinput').prop('files'),
        oversized_files = [],
        files_with_space = [],
        wrong_format_files = [],
        gb_limit = 5;

    // Check file size
    $.each(files, function (index, file) {
        if (file.size > gb_limit * Math.pow(10, 9)) {
            oversized_files.push(file.name + ' (' + (file.size / Math.pow(10, 9)).toFixed(2) + ' GB)');
        }
        if (file.name.indexOf(' ') > -1) {
            files_with_space.push(file.name)
        }
    })

    // Check if any file is oversized
    if (oversized_files.length) {
        // Alert oversized files
        alert('The following files exceed ' + gb_limit + 'GB, which is the maximum file size supported by BioJupies. Please remove them to proceed.\n\n • ' + oversized_files.join('\n • ') + '\n\nTo analyze the data, we recommend quantifying gene counts using kallisto or STAR, and uploading the generated read counts using the BioJupies table upload (https://amp.pharm.mssm.edu/biojupies/upload).');
    } else if (files_with_space.length) {
        // Alert oversized files
        alert('The following file(s) contain one or more spaces in their file names. This is currently not supported by the BioJupies alignment pipeline. Please rename them to proceed.\n\n • ' + files_with_space.join('\n • '));
    } else if (wrong_format_files.length) {
        // Alert wrong format files
        alert('BioJupies only supports alignment of files in the .fastq.gz or .fq.gz formats. The following file(s) are stored in formats which are currently not supported. Please remove or reformat them to proceed.\n\n • ' + wrong_format_files.join('\n • '));
    } else {

        // Loop through files
        $.each(files, function (index, file) {

            // Add progress bar
            // progress_bar(file['name']);
            // use simple file upload for small files and multipart otherwise
            if (file.size < 10 * 1024 * 1024) {
                $.ajax({
                    type: 'POST',
                    url: base_url+'/upload',
                    data: '{"filename": "' + file['name'] + '"}', // or JSON.stringify ({name: 'jonas'}),
                    success: function (data) {
                        var FD = new FormData();
                        for (var key in data["response"]["fields"]) {
                            FD.append(key, data["response"]["fields"][key]);
                        }
                        FD.append('file', file);

                        var filename = file['name'];

                        // Create Request
                        var xhr = new XMLHttpRequest();
                        xhr.open("POST", data["response"]["url"], true);
                        xhr.onloadstart = function (e) {
                            console.log("start")
                        }
                        xhr.onloadend = function (e) {
                            // Set complete status on progress bar
                            $('[data-filename="' + filename + '"] .progress-bar').attr('data-status', 'complete');
                            $('[data-filename="' + filename + '"] .progress-bar-text span:first-child').html('Successfully uploaded ');
                            $('[data-filename="' + filename + '"] .progress-bar-text span:last-child').html('');

                            // Activate button if all progress bars are complete
                            if ($('.progress-bar').length === $('.progress-bar[data-status="complete"]').length) {
                                $('.continue-button').prop('disabled', false).toggleClass('black white bg-white bg-blue');
                            }
                            
                            filenames.push(filename);
                            // Call FASTQ Upload Status API
                        }
                        xhr.upload.addEventListener('progress', function (evt) {
                            if (evt.lengthComputable) {
                                var progress = Math.ceil((evt.loaded / evt.total) * 100) + '%';
                                $('[data-filename="' + filename + '"] .progress-bar').html(progress);
                                $('[data-filename="' + filename + '"] .progress-bar').css('width', progress);
                            }
                        }, false);
                        xhr.send(FD);

                    },
                    contentType: "application/json",
                    dataType: 'json'
                });
            } // simple file upload
            else {
                //var file_slice = file.slice(0, 5*1024*1024)
                var chunk_size = 5*1024*1024
                var chunk_number = file.size/chunk_size
                var chunks = range(chunk_number)

                var payload = JSON.stringify({
                    "filename": file['name']
                });

                (async() => {
                    var parts = []
                    const response = await fetch(base_url+'/startmultipart', 
                    {
                        method: "POST",
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        },
                        body: payload
                    })
                    const res = await response.json();

                    await Promise.all(chunks.map(async (chunk) => {
                        var payload_part = {
                            "filename": file['name'],
                            "upload_id": res["upload_id"],
                            "part_number": chunk
                        }
                        const res_part = await fetch(base_url+'/signmultipart', 
                        {   
                            method: "POST",
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(payload_part)
                        })
                        const res_signed_part = await res_part.json();

                        fetch(res_signed_part["url"], 
                        {   
                            method: "PUT",
                            body: file.slice(chunk*chunk_size, Math.min(file.size, (chunk+1)*chunk_size)),
                        }).then(function(resp){
                            var etag = resp.headers.get("etag")
                            console.log(etag)
                            parts.push({"ETag": etag, "PartNumber": chunk})
                        })
                    })) // promise all complete
                    console.log(parts)
                    payload_complete = {
                        "filename": file['name'],
                        "upload_id": res["upload_id"],
                        "parts": parts
                    }
                    console.log(payload_complete)
                    fetch(base_url+"/completemultipart", {
                        method: "POST",
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload_complete)
                    }) // end complete
                })(); // end async
            }
        })
    }
}
