import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { HelperService } from 'src/app/shared/service/helper.service';
import { BasicService } from '../basic.service';

@Injectable({
  providedIn: 'root'
})
export class DepartmentService extends BasicService{

  constructor(
    public httpClient: HttpClient,
    public helperService: HelperService
  ) {
    super('ess', 'department', httpClient, helperService)
  }

  public getAllWithoutPagination(): Observable<any> {
    const url = `${this.serviceUrl}/get-all`;
    return this.getRequest(url);
  }
}
