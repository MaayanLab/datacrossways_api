// Upload Reads to Amazon S3 Bucket
function upload_reads() {

    // Get files
    var files = $('#fileinput').prop('files'),
        oversized_files = [],
        files_with_space = [],
        wrong_format_files = [],
        gb_limit=5;

    // Check file size
    $.each(files, function (index, file) {
        if (file.size > gb_limit*Math.pow(10, 9)) {
            oversized_files.push(file.name+' ('+(file.size/Math.pow(10,9)).toFixed(2)+' GB)');
        }
        if (file.name.indexOf(' ') > -1) {
            files_with_space.push(file.name)
        }
        //if (file.name.indexOf('.fastq.gz') === -1 && file.name.indexOf('.fq.gz') === -1) {
        //    wrong_format_files.push(file.name)
        //}
    })
    
    // Check if any file is oversized
    if (oversized_files.length) {
        // Alert oversized files
        alert('The following files exceed '+gb_limit+'GB, which is the maximum file size supported by BioJupies. Please remove them to proceed.\n\n • '+oversized_files.join('\n • ')+'\n\nTo analyze the data, we recommend quantifying gene counts using kallisto or STAR, and uploading the generated read counts using the BioJupies table upload (https://amp.pharm.mssm.edu/biojupies/upload).');
    } else if (files_with_space.length) {
        // Alert oversized files
        alert('The following file(s) contain one or more spaces in their file names. This is currently not supported by the BioJupies alignment pipeline. Please rename them to proceed.\n\n • '+ files_with_space.join('\n • '));
    } else if (wrong_format_files.length) {
        // Alert wrong format files
        alert('BioJupies only supports alignment of files in the .fastq.gz or .fq.gz formats. The following file(s) are stored in formats which are currently not supported. Please remove or reformat them to proceed.\n\n • '+ wrong_format_files.join('\n • '));
    } else {
        
        // Loop through files
        $.each(files, function(index, file) {

            // Add progress bar
            progress_bar(file['name']);

            // Get Sign Policy
            $.getJSON("/upload/api/elysium?request_type=signpolicy", function (data) {

                // Create Form
                var FD = new FormData();
                FD.append('key', data['uid'] + "/RULKgC2F4SA-${filename}");
                FD.append('AWSAccessKeyId', data['cid']);
                FD.append('acl', 'private');
                FD.append('success_action_redirect', 'success.html');
                FD.append('policy', data['policy']);
                FD.append('signature', data['signature']);
                FD.append('Content-Type', 'application/octet-stream');
                FD.append('file', file);

                // Get filename
                var filename = file['name'];

                // Create Request
                var xhr = new XMLHttpRequest();
                xhr.open("POST", "https://" + data["bucket"] + ".s3.amazonaws.com/", true);
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
                    console.log("end")

                    filenames.push(filename);
                    // Call FASTQ Upload Status API
                }
                xhr.upload.addEventListener('progress', function (evt) {
                    if (evt.lengthComputable) {
                        var progress = Math.ceil((evt.loaded / evt.total) * 100)+'%';
                        $('[data-filename="' + filename + '"] .progress-bar').html(progress);
                        $('[data-filename="' + filename + '"] .progress-bar').css('width', progress);
                    }
                }, false);
                xhr.send(FD);

            });
        })
    }
}