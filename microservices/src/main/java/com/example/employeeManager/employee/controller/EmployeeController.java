package com.example.employeeManager.employee.controller;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import javax.servlet.http.HttpServletRequest;
import javax.xml.bind.DatatypeConverter;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

import com.example.common.CommonUtil;
import com.example.common.Constants;
import com.example.common.DataTableResults;
import com.example.common.Response;
import com.example.controller.BaseController;
import com.example.employeeManager.employee.bean.EmployeeBean;
import com.example.employeeManager.employee.bo.EmployeeBO;
import com.example.employeeManager.employee.form.EmployeeForm;
import com.example.employeeManager.employee.service.EmployeeService;
import com.example.employeeManager.employeeImages.bo.EmployeeImagesBO;
import com.example.employeeManager.employeeImages.service.EmployeeImagesService;

@Controller
@RequestMapping("/v1/employee-manager/employee")
public class EmployeeController extends BaseController {

    private static String adResourceKey = "resource.employee";

    @Autowired
    private EmployeeService employeeService;
    
    @Autowired
    private EmployeeImagesService employeeImagesService;

    /**
     * findById
     * @param employeeId
     * @return
     */
    @GetMapping(path = "/{employeeId}")
    public @ResponseBody Response findById(HttpServletRequest req, @PathVariable Long employeeId) {
//        if (! permissionChecker.hasPermission("action.view", adResourceKey, req)) {
//            return Response.invalidPermission();
//        }
        EmployeeBO employeeBO = employeeService.findById(employeeId);
        if(employeeBO == null) {
            return Response.warning(Constants.RESPONSE_CODE.RECORD_DELETED);
        }
        employeeBO.setEmployeeImgUrl(employeeImagesService.getListImgUrlByEmplId(employeeId));
        return Response.success().withData(employeeBO);
    }

    /**
     * processSearch
     * @param EmployeeForm form
     * @return DataTableResults
     */
    @GetMapping(path = "/search")
    public @ResponseBody DataTableResults<EmployeeBean> processSearch(HttpServletRequest req, EmployeeForm form) {
//        if (! permissionChecker.hasPermission("action.view", adResourceKey, req)) {
//            throw new PermissionException();
//        }
        return employeeService.getDatatables(form);
    }

    /**
     * saveOrUpdate EmployeeBO
     * @param req
     * @param form
     * @return
     * @throws Exception
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public @ResponseBody Response saveOrUpdate(HttpServletRequest req, @RequestBody EmployeeForm form) throws Exception {
        Long employeeId = CommonUtil.NVL(form.getEmployeeId());
        EmployeeBO employeeBO;
        if(employeeId > 0L) {
//            if (!permissionChecker.hasPermission("action.update", adResourceKey, req)) {
//                return Response.invalidPermission();
//            }
            employeeBO = employeeService.findById(employeeId);
            if(employeeBO == null){
                return Response.warning(Constants.RESPONSE_CODE.RECORD_DELETED);
            }
            employeeBO.setModifiedDate(new Date());
            employeeBO.setModifiedBy(CommonUtil.getUserLoginName(req));
            employeeBO.setStatus(form.getStatus());
        } else {
//            if (!permissionChecker.hasPermission("action.insert", adResourceKey, req)) {
//                return Response.invalidPermission();
//            }
            employeeBO = new EmployeeBO();
            employeeBO.setCreatedDate(new Date());
            employeeBO.setCreatedBy(CommonUtil.getUserLoginName(req));
            employeeBO.setStatus(Constants.STATUS.EFFECTIVE);
        }
        employeeBO.setEmployeeCode(form.getEmployeeCode());
        employeeBO.setEmployeeName(form.getEmployeeName());
        employeeBO.setDateOfBirth(form.getDateOfBirth());
        employeeBO.setGender(form.getGender());
        employeeBO.setEmail(form.getEmail());
        employeeBO.setPhoneNumber(form.getPhoneNumber());
        employeeBO.setUserId(form.getUserId());
        employeeBO.setDepartmentId(form.getDepartmentId());
        employeeBO.setPositionId(form.getPositionId());
        employeeService.saveOrUpdate(employeeBO);
        if(employeeId == null || employeeId.equals(0L)) {
            List<EmployeeImagesBO> listEmplImages = new ArrayList<EmployeeImagesBO>();
            if(form.getEmployeeImgUrl() != null || form.getEmployeeImgUrl().size() > 0) {
                // tao folder chua anh
                File f = new File("../train-model-image/" + employeeBO.getEmployeeCode());
                if (f.mkdir()) {
                    System.out.println("Directory is created");
                }
                else {
                    System.out.println("Directory cannot be created");
                }
                // end tao folder
                int count = 0;
                for (String item : form.getEmployeeImgUrl()) {
                    EmployeeImagesBO bo = new EmployeeImagesBO();
                    bo.setEmployeeId(employeeBO.getEmployeeId());
                    bo.setEmployeeImgUrl(item);
                    listEmplImages.add(bo);
                    // save string base64 as a file to folder start
                    String base64String = item;
                    String[] strings = base64String.split(",");
                    String extension;
                    switch (strings[0]) {//check image's extension
                        case "data:image/jpeg;base64":
                            extension = "jpeg";
                            break;
                        case "data:image/png;base64":
                            extension = "png";
                            break;
                        default://should write cases for more images types
                            extension = "jpg";
                            break;
                    }
                    //convert base64 string to binary data
                    byte[] data = DatatypeConverter.parseBase64Binary(strings[1]);
                    String path = "../train-model-image/" + employeeBO.getEmployeeCode() + "/" + String.valueOf(count++) + "." + extension;
                    File file = new File(path);
                    try (OutputStream outputStream = new BufferedOutputStream(new FileOutputStream(file))) {
                        outputStream.write(data);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
                employeeImagesService.saveAll(listEmplImages);
            }
        }
        
        return Response.success(Constants.RESPONSE_CODE.SUCCESS).withData(employeeBO);
    }

    /**
     * delete
     * @param employeeId
     * @return
     */
    @DeleteMapping(path = "/{employeeId}")
    @ResponseStatus(HttpStatus.OK)
    public @ResponseBody Response delete(HttpServletRequest req, @PathVariable Long employeeId) {
//        if (! permissionChecker.hasPermission("action.delete", adResourceKey, req)) {
//            return Response.invalidPermission();
//        }
        EmployeeBO bo ;
        if(employeeId > 0L) {
            bo = employeeService.findById(employeeId);
            if(bo == null) {
                return Response.warning(Constants.RESPONSE_CODE.RECORD_DELETED);
            }
            employeeService.delete(bo);
            return Response.success(Constants.RESPONSE_CODE.DELETE_SUCCESS);
        } else {
            return Response.error(Constants.RESPONSE_CODE.ERROR);
        }
    }
}
