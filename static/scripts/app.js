$(document).ready(function(){
  const MAX_ALLOWED_WIDTH = 2000
  const MAX_ALLOWED_HEIGHT = 2000

  // Получить расширение файла
  function getFileFormat(fileName) {
    return fileName.split('.').pop()
  }


  // Поддержка загрузки изображений перетаскиваем
  const dropFileZone = document.querySelector("#file-drag")
  const uploadInput = document.querySelector('#file-upload')

  document.addEventListener('dragover', (e) => {
    e.preventDefault()
  })

  document.addEventListener('drop', (e) => {
    e.preventDefault()
  })

  dropFileZone.addEventListener("drop", function() {
    const file = event.dataTransfer?.files[0]
    if (!file) {
        return
    }

    if (file.type.startsWith("image/")) {
        uploadInput.files = event.dataTransfer.files

        uploadInput.dispatchEvent(new Event("change"))
    }
  })

  const allowedFileFormats = ['png', 'jpg']

  $('#file-upload').change(function(e){
    const uploadedFile = this.files[0]
    const fileFormat = getFileFormat(uploadedFile.name)

    if (allowedFileFormats.includes(fileFormat)) {
      $('#notimage-div').hide(2)

      $('#please-select-file-div').hide(2)

      $('#filename-div').show(2)
      $('#filename-div').html(uploadedFile.name)

      $('#file-image').show(2)
      $('#file-image').attr('src', URL.createObjectURL(uploadedFile))

      $("#download-icon").hide(2)
    } else {
      $('#notimage-div').show(2)
    }
  })

  // Изменения качества
  $('#quality-input').change(function(e){
    $('#quality-value').html(this.value + '%')
  })

  $('#file-upload-form').submit(function(e){
    e.preventDefault()

    var formData = new FormData()

    const width = $('#width_input').val()

    if(width <= 0 || width > MAX_ALLOWED_WIDTH) {
        return;
    }

    const height = $('#height_input').val()

    if (height <= 0 || height > MAX_ALLOWED_HEIGHT){
        return;
    }

    formData.append('width', $('#width_input').val())
    formData.append('height', $('#height_input').val())
    formData.append('quality', $('#quality-input').val())
    formData.append('optimisation', $('#optimisation-checkbox').is(':checked'))
    formData.append('result_format', $("#result-format").val())

    const files = $('#file-upload').prop('files')

    if (files.length > 0) {
        formData.append('file', files[0])

        $.ajax({
            url: '/upload_image',
            data: formData,
            type: 'POST',
            processData: false,
            contentType: false,
            dataType: "json",
            success: function(response) {
                $('#response-message').show(2)
                $('#response-message').html(`<h3> Изображение будет доступно по
                    <a href="/get?id=${response.image_id}"> ссылке </a></h3>
                `)

                $('#start').hide(2)
                $('#file-upload').hide(2)
                $('#file-drag').hide(2)
            }
        })
    }
  })

})