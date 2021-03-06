import {
  ChangeDetectorRef,
  Component,
  NgZone,
  OnDestroy,
  ViewChild,
  HostListener,
  Directive,
  AfterViewInit,
  OnInit
} from '@angular/core';
import { MediaMatcher } from '@angular/cdk/layout';
import { MenuItems } from '../../../shared/menu-items/menu-items';
import { Storage } from '../../../shared/service/storage.service';
import { UserToken } from '../../../core/models/user-token.model';
import { Router } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { BaseComponent } from '../../../shared/components/base-component/base-component.component';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: []
})
export class AppSidebarComponent extends BaseComponent implements OnInit, OnDestroy {
  mobileQuery: MediaQueryList;
  userInfo: UserToken;

  items: MenuItem[];
  private mobileQueryListener: () => void;

  constructor(
    changeDetectorRef: ChangeDetectorRef,
    media: MediaMatcher,
    public router: Router,
    public menuItems: MenuItems
  ) {
    super(null);
    this.mobileQuery = media.matchMedia('(min-width: 768px)');
    this.mobileQueryListener = () => changeDetectorRef.detectChanges();
    // tslint:disable-next-line: deprecation
    this.mobileQuery.addListener(this.mobileQueryListener);
    this.userInfo = Storage.getUserToken();
  }

  ngOnInit(): void {
    this.innitMenu();
  }

  ngOnDestroy(): void {
    // tslint:disable-next-line: deprecation
    this.mobileQuery.removeListener(this.mobileQueryListener);
  }

  // tslint:disable-next-line: typedef
  public userInformation() {
    this.router.navigate(['/user-info']);
  }

  // tslint:disable-next-line: typedef
  public changePassword() {
    this.router.navigate(['/user-info/change-password']);
  }

  // tslint:disable-next-line: typedef
  public logOut() {
    this.router.navigate(['/login']);
    Storage.clear();
  }
  // tslint:disable-next-line: member-ordering
  routerLink: ['/pagename'];
  // tslint:disable-next-line: typedef
  private innitMenu() {
    // TODO Khai b??o c??c url tr??n side-sidebar
    this.items = [
      {
        label: 'Trang ch???',
        icon: 'pi pi-home',
        routerLink: ['/dashboard']
      },
      {
        label: 'Qu???n l?? user',
        icon: 'pi pi-user',
        routerLink: ['/user']
      },
      {
        label: 'Qu???n l?? nh??n vi??n',
        icon: 'pi pi-users',
        items: [
          {
            label: 'Qu???n l?? ph??ng ban',
            icon: 'pi pi-th-large',
            routerLink: ['/employee-manager/departments']
          },
          {
            label: 'Qu???n l?? nh??n vi??n',
            icon: 'pi pi-th-large',
            routerLink: ['/employee-manager/employees']
          },
          {
            label: 'Qu???n l?? ch???c v???',
            icon: 'pi pi-th-large',
            routerLink: ['/employee-manager/positions']
          }
        ]
      },
      {
        label: 'Qu???n l?? ch???m c??ng',
        icon: 'pi pi-chart-line',
        routerLink: ['/timekeeping-manager']
      },
      {
        label: 'Qu???n l?? ph??n quy???n',
        icon: 'pi pi-cog',
        routerLink: ['/role-manager']
      }
    ];
  }
}
