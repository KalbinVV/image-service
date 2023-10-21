$(document).ready(function(){
  // Получить расширение файла
  function getFileFormat(fileName) {
    return fileName.split('.').pop()
  }

  const allowedFileFormats = ['png', 'png']

  $('#file-upload').change(function(e){
    const uploadedFile = this.files[0]
    const fileFormat = getFileFormat(uploadedFile.name)

    if (allowedFileFormats.includes(fileFormat)) {
      $('#notimage_div').hide(2)

      $('#please_select_file_div').hide(2)

      $('#file_name_div').show(2)
      $('#file_name_div').html(uploadedFile.name)
    } else {
      $('#notimage_div').show(2)
    }
  })

})