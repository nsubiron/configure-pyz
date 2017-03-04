#include "mylib_dependency.h"

#include "EmbeddedData.h"

#include <iostream>
#include <string>

namespace mylib_dependency {

  void do_the_test() {
    std::string str{
        mylib_dependency_resources_data_txt,
        mylib_dependency_resources_data_txt + mylib_dependency_resources_data_txt_len};
    std::cout << str;
  }

}
