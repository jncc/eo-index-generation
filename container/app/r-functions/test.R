renv::activate()

helloDave <- function(name) {
    paste("hello dave: ", name)
}

keyValuePair <- function() {
    line1 = "This is the first line."

    list <- list(line1 = line1,
             line2 = "Now, the second line." )
    
    json <- rjson::toJSON(list)

    return(json)
}

mapTest <- function() {
    stuff <- list("ab", "cd", "ef")
    other <- list("xy", "py", "ts")

    output <- purrr::map2(other, stuff, function(x, y){
        result <- paste0(x, y)
    })

   json <- rjson::toJSON(output)    

   return(json)
}