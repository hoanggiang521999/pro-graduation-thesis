import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { HelperService } from 'src/app/shared/service/helper.service';
import { BasicService } from '../basic.service';

@Injectable({
  providedIn: 'root'
})
export class TimekeepingService extends BasicService {

  constructor(
    public helperService: HelperService,
    public httpClient: HttpClient
  ) {
    super('ess', 'timekeeping', httpClient, helperService);
  }
}
